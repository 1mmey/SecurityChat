
# 导入 FastAPI 框架和相关工具
from fastapi import FastAPI, Depends, HTTPException, APIRouter
# 导入 SQLAlchemy 的 Session 用于类型提示
from sqlalchemy.orm import Session

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


# --- 用户 API 路由器 ---
# 创建一个 API 路由器，用于组织与用户相关的 API 端点
router = APIRouter(
    prefix="/users",  # 为这个路由器下的所有路径添加 "/users" 前缀
    tags=["Users"],   # 在 API 文档中为这些端点分组
)

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户的 API 端点。
    - **user**: 请求体，需要符合 `schemas.UserCreate` 的结构。
    - **db**: 依赖注入，自动获取数据库会话。
    """
    # 检查用户名是否已存在
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 调用 crud 函数创建用户
    return crud.create_user(db=db, user=user)

# 将用户路由器包含到主应用中
app.include_router(router)

# 你可以在这里添加更多的路由器，例如用于认证、消息等
# from .routers import auth_router, messages_router
# app.include_router(auth_router)
# app.include_router(messages_router)

