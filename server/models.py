from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    public_key = Column(Text)
    private_key = Column(Text)
    is_online = Column(Boolean, default=False)
    last_login = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

class Friendship(Base):
    __tablename__ = "friendships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())

class FriendRequest(Base):
    __tablename__ = "friend_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, default="")
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    message_type = Column(String, default="text")
    is_encrypted = Column(Boolean, default=False)
    is_p2p = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class P2PInfo(Base):
    __tablename__ = "p2p_info"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    peer_id = Column(String, unique=True)
    ip_address = Column(String)
    port = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class FriendRequestCreate(BaseModel):
    receiver_id: int
    message: str = ""

class FriendRequestHandle(BaseModel):
    request_id: int
    action: str

class P2PInfoUpdate(BaseModel):
    peer_id: str
    ip_address: str
    port: int

class P2PMessageSave(BaseModel):
    sender_id: int
    receiver_id: int
    content: str
    message_type: str = "text"
    is_encrypted: bool = False