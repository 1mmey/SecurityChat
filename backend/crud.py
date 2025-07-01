from typing import Optional
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

def create_user(db: Session, user_data: schemas.UserCreate):
    """
    在数据库中创建新用户
    :param db: 数据库会话
    :param user_data: 包含用户信息的 Pydantic 模型 (UserCreate)
    :return: 创建的 User 对象
    """
    # 从传入的 Pydantic 模型中获取明文密码，并进行哈希处理
    hashed_password = auth.get_password_hash(user_data.password)
    
    # 使用 Pydantic 模型的数据和哈希后的密码，创建一个 SQLAlchemy User 模型实例
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        public_key=user_data.public_key
    )
    
    # 将新用户添加到会话中
    db.add(db_user)
    # 提交事务，将更改写入数据库
    db.commit()
    # 刷新 db_user 实例，以获取数据库生成的新数据（如 ID）
    db.refresh(db_user)
    return db_user

def update_user_status(db: Session, user: models.User, is_online: bool, ip_address: Optional[str] = None, port: Optional[int] = None):
    """
    更新用户的在线状态、IP地址和端口号
    :param db: 数据库会话
    :param user: 要更新的 User 对象
    :param is_online: 是否在线
    :param ip_address: IP 地址
    :param port: 端口号
    :return: 更新后的 User 对象
    """
    user.is_online = is_online  # type: ignore
    user.ip_address = ip_address  # type: ignore
    user.port = port  # type: ignore
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# --- 联系人相关的 CRUD (待实现) ---

def add_contact(db: Session, user_id: int, friend_id: int):
    """
    在数据库中添加好友关系
    :param db: 数据库会话
    :param user_id: 当前用户的 ID
    :param friend_id: 要添加的好友的 ID
    :return: 创建的 Contact 对象
    """
    # 检查好友关系是否已经存在
    existing_contact = db.query(models.Contact).filter(
        models.Contact.user_id == user_id,
        models.Contact.friend_id == friend_id
    ).first()
    
    if existing_contact:
        return existing_contact

    db_contact = models.Contact(
        user_id=user_id,
        friend_id=friend_id,
        status="accepted"  # 默认为直接接受
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    根据用户ID获取其好友列表
    :param db: 数据库会话
    :param user_id: 用户ID
    :param skip: 分页查询的起始位置
    :param limit: 每页的数量
    :return: 联系人列表
    """
    return db.query(models.Contact).filter(models.Contact.user_id == user_id).offset(skip).limit(limit).all()

# --- 消息相关的 CRUD (待实现) ---