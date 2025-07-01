# 导入 FastAPI 框架和相关工具
from fastapi import FastAPI, Depends, HTTPException, APIRouter, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from fastapi_utils.tasks import repeat_every
# 导入 SQLAlchemy 的 Session 用于类型提示
from sqlalchemy.orm import Session
from typing import List

# 从同级目录导入我们创建的模块
from . import crud, models, schemas, auth
from .database import engine, get_db
from .connection_manager import manager

# --- 数据库初始化 ---
# 这行代码会根据我们在 models.py 中定义的 ORM 模型，在数据库中创建相应的表。
# 它只在表不存在时创建，如果表已存在则不会有操作。
models.Base.metadata.create_all(bind=engine)

# --- FastAPI 应用实例 ---
# 创建一个 FastAPI 应用实例
app = FastAPI(
    title="安全即时通讯系统 API",
    description="这是大型程序设计实践项目的后端 API 文档。",
    version="0.1.0",
)

# --- CORS 中间件配置 ---
# origins 列表指定了允许访问我们后端 API 的来源。
# ["*"] 是一个通配符，表示允许任何来源的请求。
# 这在开发阶段比较方便，但在生产环境中应该设置为更具体的前端地址。
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许访问的源
    allow_credentials=True,  # 支持 cookie
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有标头
)

# --- 后台定时任务 ---
@app.on_event("startup")
@repeat_every(seconds=60, wait_first=True)
def cleanup_offline_users():
    """
    每分钟运行一次的后台任务，用于清理离线用户。
    它会检查所有标记为在线的用户，如果他们最后一次在线时间是2分钟前，
    就将他们标记为离线。
    """
    db: Session = next(get_db())
    timeout_threshold = datetime.utcnow() - timedelta(minutes=2)
    
    # 查找所有在线但已超时的用户
    offline_users = db.query(models.User).filter(
        models.User.is_online == True,
        models.User.last_seen < timeout_threshold
    ).all()

    if offline_users:
        user_names = [user.username for user in offline_users]
        print(f"后台任务：检测到超时的用户: {user_names}，将其标记为离线。")
        for user in offline_users:
            user.is_online = False  # type: ignore
        db.commit()

# --- 认证 API (登录) ---
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # 从数据库中通过用户名查找用户
    user = crud.get_user_by_username(db, username=form_data.username)
    # 验证用户是否存在以及密码是否正确
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从请求中获取客户端的 IP 地址和端口号
    client_ip = "127.0.0.1"  # 默认值
    client_port = 0 # 默认值
    if request.client:
        client_ip = request.client.host
        client_port = request.client.port
    
    # 更新用户的在线状态、IP 和端口
    crud.update_user_status(db=db, user=user, is_online=True, ip_address=client_ip, port=client_port)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # 返回令牌
    return {"access_token": access_token, "token_type": "bearer"}

# --- "我" (当前用户) 相关的 API ---
@app.put("/me/connection-info", response_model=schemas.UserPublic)
def update_my_connection_info(
    info_update: schemas.ConnectionInfoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    更新当前用户的连接信息（IP、端口）并将会话标记为在线。
    客户端应该在登录后和需要更新网络状态时调用此接口。
    """
    client_ip = "127.0.0.1"
    if request.client:
        client_ip = request.client.host

    updated_user = crud.update_user_status(
        db=db,
        user=current_user,
        is_online=True,
        ip_address=client_ip,
        port=info_update.port
    )
    return updated_user

@app.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    处理用户登出，将其在线状态设置为 False。
    """
    crud.update_user_status(db=db, user=current_user, is_online=False)
    return {"message": "Successfully logged out"}

# --- 用户 API 路由器 ---
# 创建一个 API 路由器，用于组织与用户相关的 API 端点
router = APIRouter(
    prefix="/users",  # 为这个路由器下的所有路径添加 "/users" 前缀
    tags=["Users"],   # 在 API 文档中为这些端点分组
)

# --- 联系人 API 路由器 ---
contact_router = APIRouter(
    prefix="/me/contacts",
    tags=["Contacts"],
    dependencies=[Depends(auth.get_current_user)] # 保护此路由下的所有端点
)

@router.post("/", response_model=schemas.User)
def create_user(user_data: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    创建新用户的 API 端点。
    - **user_data**: 请求体，需要符合 `schemas.UserCreate` 的结构。
    - **request**: FastAPI 的请求对象，用于获取客户端信息。
    - **db**: 依赖注入，自动获取数据库会话。
    """
    # 检查用户名是否已存在
    db_user = crud.get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    db_user_email = crud.get_user_by_email(db, email=user_data.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 从请求中获取客户端的 IP 地址
    client_ip = "127.0.0.1" # 默认值
    if request.client:
        client_ip = request.client.host

    # 调用 crud 函数创建用户，并传入 IP 地址
    return crud.create_user(db=db, user_data=user_data, ip_address=client_ip)

@router.get("/{username}/connection-info", response_model=schemas.UserConnectionInfo)
def get_user_connection_info(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    获取指定用户的连接信息（公钥、IP、端口）以用于P2P通信。
    只有当目标用户在线时才能获取成功。
    """
    target_user = crud.get_user_by_username(db, username=username)

    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not target_user.is_online:  # type: ignore
        raise HTTPException(status_code=404, detail="用户当前不在线")

    return target_user

@contact_router.post("/", response_model=schemas.Contact)
def add_new_contact(
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    添加新的好友。
    """
    # 检查要添加的好友是否存在
    friend = crud.get_user(db, user_id=contact.friend_id)
    if not friend:
        raise HTTPException(status_code=404, detail="要添加的好友不存在")

    # 确保当前用户有ID，并让类型检查器满意
    assert current_user.id is not None, "当前用户没有ID"

    # 不能添加自己为好友
    if current_user.id == contact.friend_id:  # type: ignore
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    return crud.add_contact(db=db, user_id=current_user.id, friend_id=contact.friend_id)  # type: ignore

@contact_router.get("/", response_model=List[schemas.Contact])
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    获取当前用户的好友列表。
    """
    contacts = crud.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit) # type: ignore
    return contacts

@contact_router.get("/online", response_model=List[schemas.UserConnectionInfo])
def get_online_friends_info(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    高效地获取当前用户所有在线好友的连接信息列表。
    """
    assert current_user.id is not None
    online_friends = crud.get_online_friends(db, user_id=current_user.id) # type: ignore
    return online_friends

# --- 消息 API 路由器 ---
message_router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
    dependencies=[Depends(auth.get_current_active_user)]
)

@message_router.post("/", response_model=schemas.Message)
def send_offline_message(
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    发送离线消息。
    - 检查接收者是否存在。
    - 如果存在，则将加密消息存储到数据库。
    """
    recipient = crud.get_user_by_username(db, username=message_data.recipient_username)
    if not recipient:
        raise HTTPException(status_code=404, detail="接收者用户不存在")

    # 确保当前用户和接收者都有 ID
    assert current_user.id is not None
    assert recipient.id is not None

    return crud.create_message(
        db=db,
        sender_id=current_user.id, # type: ignore
        receiver_id=recipient.id, # type: ignore
        encrypted_content=message_data.encrypted_content
    )

@message_router.get("/", response_model=List[schemas.Message])
def get_my_offline_messages(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    获取当前用户的所有离线消息，并在获取后将其标记为已读。
    """
    assert current_user.id is not None

    # 1. 获取所有未读消息
    unread_messages = crud.get_unread_messages_for_user(db, user_id=current_user.id) # type: ignore
    
    if not unread_messages:
        return []

    # 2. 将这些消息标记为已读
    message_ids = [msg.id for msg in unread_messages]
    crud.mark_messages_as_read(db, message_ids=message_ids) # type: ignore

    # 3. 返回这些消息
    return unread_messages

##
@router.delete("/users/self", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int,db: Session = Depends(get_db),current_user: schemas.User = Depends(models.get_current_user)):
    
    """硬删除用户（物理删除，不可恢复）"""
    # 1. 查询用户是否存在
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. 检查权限（示例：仅管理员或用户本人可删除）
    if current_user.id != db_user.id:           #and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 3. 执行硬删除（物理删除）
    db.delete(db_user)
    db.commit()
    
    return None  # 返回 204 No Content 表示删除成功   

# 将用户路由器包含到主应用中
app.include_router(router)
app.include_router(contact_router)
app.include_router(message_router)

# --- WebSocket 端点 ---
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user_from_ws)
):
    if not user:
        # 如果get_current_user_from_ws返回None，则不建立连接
        # get_current_user_from_ws 内部已经处理了拒绝逻辑
        return

    await manager.connect(websocket, user.id) # type: ignore
    await manager.broadcast(f"用户 {user.username} 加入了聊天", disconnected_user_id=user.id) # type: ignore
    try:
        while True:
            data = await websocket.receive_text()
            # 这里可以处理接收到的消息，例如，转发给特定用户
            # 为了简单起见，我们只是广播它
            await manager.broadcast(f"{user.username}: {data}")
    except WebSocketDisconnect:
        print(f"用户 {user.username} 的WebSocket连接断开")
    finally:
        manager.disconnect(user.id) # type: ignore
        print(f"用户 {user.username} 已离开")
        # 广播用户离开的消息，并排除当前用户
        await manager.broadcast(f"用户 {user.username} 已离开", disconnected_user_id=user.id) # type: ignore

# 你可以在这里添加更多的路由器，例如用于认证、消息等
# from .routers import auth_router, messages_router
# app.include_router(auth_router)
# app.include_router(messages_router)

# 空编辑，用于触发 uvicorn 重载

