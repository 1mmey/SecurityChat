# 导入 SQLAlchemy 的 Session 用于类型提示
from sqlalchemy.orm import Session
# 从同级目录导入 models, schemas, 和 auth 模块
from . import models, schemas, auth

# --- 用户相关的 CRUD (Create, Read, Update, Delete) 操作 ---

def get_user(db: Session, user_id: int):
    """
    根据用户 ID 从数据库中查询用户
    :param db: 数据库会话
    :param user_id: 用户 ID
    :return: User 对象或 None
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    """
    根据用户名从数据库中查询用户
    :param db: 数据库会话
    :param username: 用户名
    :return: User 对象或 None
    """
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """
    根据邮箱从数据库中查询用户
    :param db: 数据库会话
    :param email: 邮箱地址
    :return: User 对象或 None
    """
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    从数据库中查询多个用户（支持分页）
    :param db: 数据库会话
    :param skip: 跳过的记录数
    :param limit: 返回的最大记录数
    :return: User 对象列表
    """
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """
    在数据库中创建新用户
    :param db: 数据库会话
    :param user: 包含用户信息的 Pydantic 模型 (UserCreate)
    :return: 创建的 User 对象
    """
    # 使用 auth 模块中的函数获取密码的哈希值
    hashed_password = auth.get_password_hash(user.password)
    # 创建一个 SQLAlchemy User 模型实例
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        public_key=user.public_key
    )
    # 将新用户添加到会话中
    db.add(db_user)
    # 提交事务，将更改写入数据库
    db.commit()
    # 刷新 db_user 实例，以获取数据库生成的新数据（如 ID）
    db.refresh(db_user)
    return db_user

# --- 联系人相关的 CRUD (待实现) ---

# --- 消息相关的 CRUD (待实现) ---