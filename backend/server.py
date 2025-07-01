# 导入 FastAPI 框架和相关工具
from fastapi import FastAPI, Depends, HTTPException, APIRouter, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
# 导入 SQLAlchemy 的 Session 用于类型提示
from sqlalchemy.orm import Session
from typing import List

# 从同级目录导入我们创建的模块
from . import crud, models, schemas, auth
from .database import engine, get_db

# --- 数据库初始化 ---
# 这行代码会根据我们在 models.py 中定义的 ORM 模型，在数据库中创建相应的表。
# 它只在表不存在时创建，如果表已存在则不会有任何操作。
models.Base.metadata.create_all(bind=engine)

# --- FastAPI 应用实例 ---
# 创建一个 FastAPI 应用实例
app = FastAPI(
    title="安全即时通讯系统 API",
    description="这是大型程序设计实践项目的后端 API 文档。",
    version="0.1.0",
)


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


##
@router.delete("/users/{user_id}", status_code=204)
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

# 你可以在这里添加更多的路由器，例如用于认证、消息等
# from .routers import auth_router, messages_router
# app.include_router(auth_router)
# app.include_router(messages_router)

