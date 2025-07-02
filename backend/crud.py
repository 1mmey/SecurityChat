from typing import Optional
from datetime import datetime
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

def search_users_by_username(db: Session, username_query: str, skip: int = 0, limit: int = 10):
    """
    根据用户名模糊搜索用户
    :param db: 数据库会话
    :param username_query: 用户名搜索关键词
    :param skip: 跳过的记录数
    :param limit: 返回的最大记录数
    :return: User 对象列表
    """
    return db.query(models.User).filter(
        models.User.username.ilike(f"%{username_query}%")
    ).offset(skip).limit(limit).all()

def create_user(db: Session, user_data: schemas.UserCreate, ip_address: str):
    """
    在数据库中创建新用户
    :param db: 数据库会话
    :param user_data: 包含用户信息的 Pydantic 模型 (UserCreate)
    :param ip_address: 用户的IP地址
    :return: 创建的 User 对象
    """
    # 从传入的 Pydantic 模型中获取明文密码，并进行哈希处理
    hashed_password = auth.get_password_hash(user_data.password)
    
    # 使用 Pydantic 模型的数据和哈希后的密码，创建一个 SQLAlchemy User 模型实例
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        public_key=user_data.public_key,
        ip_address=ip_address  # 记录用户的IP地址
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
    
    # 如果用户是在线状态，则更新 last_seen 时间戳
    if is_online:
        user.last_seen = datetime.utcnow() # type: ignore
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# --- 联系人相关的 CRUD (待实现) ---

def add_contact(db: Session, user_id: int, friend_id: int) -> Optional[models.Contact]:
    """
    在数据库中创建一条好友请求 (status='pending')
    :param db: 数据库会话
    :param user_id: 发起请求的用户的 ID
    :param friend_id: 被请求的用户的 ID
    :return: 创建的 Contact 对象或 None
    """
    # 检查反向请求是否已存在且被接受，或者自己是否已发送过请求
    existing_contact = db.query(models.Contact).filter(
        ((models.Contact.user_id == user_id) & (models.Contact.friend_id == friend_id)) |
        ((models.Contact.user_id == friend_id) & (models.Contact.friend_id == user_id) & (models.Contact.status == "accepted"))
    ).first()
    
    if existing_contact:
        return None # 如果关系已存在，则不进行任何操作

    # 检查自己是否是对方
    if user_id == friend_id:
        return None

    # 检查对方用户是否存在
    friend_user = get_user(db, friend_id)
    if not friend_user:
        return None

    db_contact = models.Contact(
        user_id=user_id,
        friend_id=friend_id,
        status="pending"  # 默认为待处理
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    根据用户ID获取其已接受的好友列表 (status='accepted')
    :param db: 数据库会话
    :param user_id: 用户ID
    :param skip: 分页查询的起始位置
    :param limit: 每页的数量
    :return: 联系人列表
    """
    return db.query(models.Contact).filter(
        models.Contact.user_id == user_id,
        models.Contact.status == "accepted"
    ).offset(skip).limit(limit).all()

def get_pending_requests(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    根据用户ID获取其收到的、待处理的好友请求列表
    :param db: 数据库会话
    :param user_id: 用户ID (被请求者)
    :param skip: 分页查询的起始位置
    :param limit: 每页的数量
    :return: 联系人列表 (请求)
    """
    return db.query(models.Contact).filter(
        models.Contact.friend_id == user_id,
        models.Contact.status == "pending"
    ).offset(skip).limit(limit).all()

def get_contact_request(db: Session, user_id: int, friend_id: int) -> Optional[models.Contact]:
    """查找特定的好友关系/请求"""
    return db.query(models.Contact).filter(
        models.Contact.user_id == user_id,
        models.Contact.friend_id == friend_id
    ).first()

def update_contact_status(db: Session, user_id: int, friend_id: int, status: str) -> Optional[models.Contact]:
    """
    更新好友关系的状态。主要用于接受好友请求。
    如果接受 (status='accepted')，则创建反向关系。
    """
    # 找到别人发给自己的请求: user_id=friend_id, friend_id=user_id
    contact_request = db.query(models.Contact).filter(
        models.Contact.user_id == friend_id,
        models.Contact.friend_id == user_id
    ).first()

    if not contact_request:
        return None # 没有找到请求

    contact_request.status = status # type: ignore
    
    if status == "accepted":
        # 如果是接受请求，则创建一条反向的、已接受的好友关系，使关系双向化
        reciprocal_contact = get_contact_request(db, user_id=user_id, friend_id=friend_id)
        if not reciprocal_contact:
            reciprocal_contact = models.Contact(
                user_id=user_id, 
                friend_id=friend_id, 
                status="accepted"
            )
            db.add(reciprocal_contact)

    db.commit()
    db.refresh(contact_request)
    return contact_request

def delete_contact(db: Session, user_id: int, friend_id: int) -> bool:
    """
    删除两个用户之间的好友关系（双向删除）
    可用于拒绝好友请求或删除好友
    """
    # 查询正向和反向的所有关系
    contacts_to_delete = db.query(models.Contact).filter(
        ((models.Contact.user_id == user_id) & (models.Contact.friend_id == friend_id)) |
        ((models.Contact.user_id == friend_id) & (models.Contact.friend_id == user_id))
    ).all()

    if not contacts_to_delete:
        return False # 没有找到关系

    for contact in contacts_to_delete:
        db.delete(contact)
    
    db.commit()
    return True

def get_online_friends(db: Session, user_id: int) -> list[models.User]:
    """
    获取指定用户的所有在线好友。
    """
    # 步骤 1: 获取当前用户所有已接受的好友的 ID 列表
    friend_ids_query = db.query(models.Contact.friend_id).filter(
        models.Contact.user_id == user_id,
        models.Contact.status == "accepted"
    )
    friend_ids = [item[0] for item in friend_ids_query.all()]

    if not friend_ids:
        return []

    # 步骤 2: 从好友 ID 列表中，查询所有在线的用户
    online_friends = db.query(models.User).filter(
        models.User.id.in_(friend_ids),
        models.User.is_online == True
    ).all()

    return online_friends

# --- 消息相关的 CRUD ---

def create_message(db: Session, sender_id: int, receiver_id: int, encrypted_content: str) -> models.Message:
    """
    在数据库中创建一条新的离线消息。
    """
    db_message = models.Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        encrypted_content=encrypted_content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_unread_messages_for_user(db: Session, user_id: int) -> list[models.Message]:
    """
    获取指定用户的所有未读离线消息。
    """
    messages = db.query(models.Message).filter(
        models.Message.receiver_id == user_id,
        models.Message.is_read == False
    ).all()
    return messages

def mark_messages_as_read(db: Session, message_ids: list[int]):
    """
    将一组消息标记为已读。
    """
    db.query(models.Message).filter(
        models.Message.id.in_(message_ids)
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()