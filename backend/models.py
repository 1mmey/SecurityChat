# 导入 SQLAlchemy 的相关模块
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# 从同级目录的 database.py 导入 Base 类
from .database import Base

# 定义用户模型 (User Model)
class User(Base):
    __tablename__ = "users"  # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True)  # 用户ID，主键，带索引
    username = Column(String, unique=True, index=True, nullable=False)  # 用户名，唯一，带索引，不为空
    email = Column(String, unique=True, index=True, nullable=False)  # 邮箱，唯一，带索引，不为空
    password_hash = Column(String, nullable=False)  # 存储哈希后的密码，不为空
    public_key = Column(Text, nullable=False)  # 用户的公钥，不为空
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间，带时区，默认为当前时间

    # --- 关系定义 (Relationships) ---
    # 一个用户可以发送多条消息
    sent_messages = relationship("Message", foreign_keys="[Message.sender_id]", back_populates="sender")
    # 一个用户可以接收多条消息
    received_messages = relationship("Message", foreign_keys="[Message.receiver_id]", back_populates="receiver")
    # 一个用户可以有多个联系人
    contacts = relationship("Contact", foreign_keys="[Contact.user_id]", back_populates="user")

# 定义联系人/好友关系模型 (Contact Model)
class Contact(Base):
    __tablename__ = "contacts"  # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True)  # 关系ID，主键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 用户自己的ID，外键关联到 users 表
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 好友的ID，外键关联到 users 表
    status = Column(String, default="pending", nullable=False)  # 好友关系状态 (例如: 'pending', 'accepted', 'blocked')
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间

    # --- 关系定义 (Relationships) ---
    # 关联到发起好友请求的用户
    user = relationship("User", foreign_keys=[user_id], back_populates="contacts")
    # 关联到被添加的好友
    friend = relationship("User", foreign_keys=[friend_id])

    # 定义一个联合唯一约束，确保 (user_id, friend_id) 的组合是唯一的，防止重复添加好友
    __table_args__ = (UniqueConstraint('user_id', 'friend_id', name='_user_friend_uc'),)

# 定义消息模型 (Message Model)
class Message(Base):
    __tablename__ = "messages"  # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True)  # 消息ID，主键
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 发送者ID，外键
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 接收者ID，外键
    encrypted_content = Column(Text, nullable=False)  # 加密后的消息内容
    sent_at = Column(DateTime(timezone=True), server_default=func.now())  # 发送时间
    is_read = Column(Boolean, default=False)  # 消息是否已读

    # --- 关系定义 (Relationships) ---
    # 关联到发送者
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    # 关联到接收者
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")