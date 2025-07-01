# 后端代码
## api_test.py
```python
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

# --- Helper Functions ---

def register_user(username, email, password):
    """Helper to register a user."""
    url = f"{BASE_URL}/users/"
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "public_key": f"key_for_{username}"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(user_data), headers=headers)
    return response

def login_user(username, password):
    """Helper to log in a user and get a token."""
    url = f"{BASE_URL}/token"
    login_data = {"username": username, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=login_data, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def add_contact(token, friend_id):
    """Helper to add a contact."""
    url = f"{BASE_URL}/me/contacts/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"friend_id": friend_id}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response

def get_contacts(token):
    """Helper to get the contacts list."""
    url = f"{BASE_URL}/me/contacts/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response

# --- Main Test Execution ---

if __name__ == "__main__":
    # Define two users
    user1_name = f"user1_{int(time.time())}"
    user2_name = f"user2_{int(time.time())}"
    user1_email = f"{user1_name}@example.com"
    user2_email = f"{user2_name}@example.com"
    password = "password123"

    # 1. Register User 1
    print(f"--- 1. Registering {user1_name} ---")
    resp1 = register_user(user1_name, user1_email, password)
    print(f"Status: {resp1.status_code}, Response: {resp1.text}")
    assert resp1.status_code == 200, "Failed to register user1"
    user1_id = resp1.json()["id"]
    print(f"✅ {user1_name} registered with ID: {user1_id}\n")

    # 2. Register User 2
    print(f"--- 2. Registering {user2_name} ---")
    resp2 = register_user(user2_name, user2_email, password)
    print(f"Status: {resp2.status_code}, Response: {resp2.text}")
    assert resp2.status_code == 200, "Failed to register user2"
    user2_id = resp2.json()["id"]
    print(f"✅ {user2_name} registered with ID: {user2_id}\n")

    # 3. User 1 logs in
    print(f"--- 3. Logging in as {user1_name} ---")
    token1 = login_user(user1_name, password)
    print(f"Token received: {'Yes' if token1 else 'No'}")
    assert token1 is not None, "Failed to log in as user1"
    print(f"✅ {user1_name} logged in successfully\n")

    # 4. User 1 adds User 2 as a contact
    print(f"--- 4. {user1_name} adds {user2_name} as a contact ---")
    resp_add = add_contact(token1, user2_id)
    print(f"Status: {resp_add.status_code}, Response: {resp_add.text}")
    assert resp_add.status_code == 200, "Failed to add contact"
    print(f"✅ {user1_name} successfully added {user2_name} as a contact!\n")

    # 5. User 1 gets their contact list
    print(f"--- 5. {user1_name} gets their contact list ---")
    resp_get = get_contacts(token1)
    print(f"Status: {resp_get.status_code}, Response: {resp_get.text}")
    assert resp_get.status_code == 200, "Failed to get contact list"
    
    contacts_list = resp_get.json()
    assert isinstance(contacts_list, list), "Contacts response is not a list"
    assert len(contacts_list) > 0, "Contacts list is empty"
    
    friend_ids = [c["friend_id"] for c in contacts_list]
    assert user2_id in friend_ids, "User2 is not in the contact list"
    
    print(f"✅ {user1_name}'s contact list correctly contains {user2_name}!")

    print("\n🎉 All contact management tests passed! 🎉") 
```

## auth.py

```python
# 导入 passlib 用于密码哈希
from passlib.context import CryptContext
# 导入 jose 用于 JWT (JSON Web Tokens) 操作
from jose import JWTError, jwt
# 导入 datetime 用于处理时间，计算令牌过期时间
from datetime import datetime, timedelta
# 导入 FastAPI 的依赖项和异常处理
from fastapi import Depends, HTTPException, status
# 导入 FastAPI 的 OAuth2 密码模式
from fastapi.security import OAuth2PasswordBearer
# 从同级目录的 schemas.py 导入 TokenData 模型
from . import schemas
from . import crud, models
from .database import get_db
from sqlalchemy.orm import Session

# --- 密码哈希部分 ---

# 创建一个 CryptContext 实例，指定使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 验证密码函数
def verify_password(plain_password, hashed_password):
    """
    验证明文密码是否与哈希后的密码匹配
    :param plain_password: 明文密码
    :param hashed_password: 哈希后的密码
    :return: 布尔值，匹配为 True，否则为 False
    """
    return pwd_context.verify(plain_password, hashed_password)

# 获取密码的哈希值
def get_password_hash(password):
    """
    计算给定密码的哈希值
    :param password: 明文密码
    :return: 哈希后的密码字符串
    """
    return pwd_context.hash(password)


# --- JWT 令牌部分 ---

# JWT 的密钥。在生产环境中，应使用更复杂的密钥，并从环境变量中加载，而不是硬编码
SECRET_KEY = "a_very_secret_key_for_our_chat_app"
# 使用的签名算法
ALGORITHM = "HS256"
# 访问令牌的过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 创建一个 OAuth2PasswordBearer 实例
# tokenUrl="token" 指明了客户端应该向哪个 URL 发送用户名和密码以获取令牌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 创建访问令牌
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    根据给定的数据和过期时间创建 JWT 访问令牌
    :param data: 要编码到令牌中的数据 (payload)
    :param expires_delta: 令牌的有效期
    :return: 编码后的 JWT 字符串
    """
    to_encode = data.copy()
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    # 编码 JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# FastAPI 依赖项：获取当前用户
# 这个函数会从请求头中提取令牌，解码并验证它
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 定义凭证无效时的异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码 JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 从 payload 中获取用户名
        username_from_payload = payload.get("sub")
        if username_from_payload is None or not isinstance(username_from_payload, str):
            raise credentials_exception
        username: str = username_from_payload
        # 将用户名存入 TokenData 模型
        token_data = schemas.TokenData(username=username)
    except JWTError:
        # 如果解码失败，则抛出凭证无效异常
        raise credentials_exception
    
    # 在一个完整的应用中，你还需要从数据库中获取用户信息
    # user = get_user(db, username=token_data.username)
    # if user is None:
    #     raise credentials_exception
    
    # 目前，我们只返回包含用户名的 token_data
    return token_data

# 新的依赖项：获取当前数据库中的活动用户对象
def get_current_active_user(
    current_user_data: schemas.TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> models.User:
    if current_user_data.username is None:
        # 这个异常理论上不会被触发，因为 get_current_user 已经检查过了
        # 但这可以让类型检查器满意
        raise HTTPException(status_code=401, detail="无法验证凭据")
    
    user = crud.get_user_by_username(db, username=current_user_data.username)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
```

## crud.py
```python
from typing import Optional
# 导入 SQLAlchemy 的 Session 用于类型提示
from sqlalchemy.orm import Session
# 从同级目录导入 models, schemas, 和 auth 模块
from . import models, schemas, auth,database

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta

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
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# 获取当前用户自身的信息
'''
def get_current_user(token: str = Depends(auth.oauth2_scheme),db: Session = Depends(database.get_db)) -> models.User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    
    user.last_login = datetime.now()
    db.commit()
    
    return schemas.User.from_orm(user) # '''

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
```

## databases.py
```python
# 导入 SQLAlchemy 的相关模块
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 定义数据库连接 URL
# 这里我们使用 SQLite，数据库文件名为 chat.db
# 如果要使用 PostgreSQL，可以注释掉下面的行并取消注释相应的行
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# 创建数据库引擎
# connect_args={"check_same_thread": False} 是 SQLite 特有的配置，允许在多线程中使用
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建一个数据库会话类 (SessionLocal)
# autocommit=False: 事务不会自动提交
# autoflush=False: 会话不会自动将更改刷新到数据库
# bind=engine: 将会话绑定到我们创建的数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个基础模型类 (Base)，我们定义的 ORM 模型将继承这个类
Base = declarative_base()

# FastAPI 依赖项：获取数据库会话
# 这个函数会在每个请求中创建一个新的数据库会话，并在请求结束后关闭它
def get_db():
    db = SessionLocal()  # 创建会话实例
    try:
        yield db  # 使用 yield 将会话提供给路径操作函数
    finally:
        db.close()  # 确保在请求处理完毕后关闭会话
```

## models.py
```python
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
    is_online = Column(Boolean, default=False) # 用户是否在线
    ip_address = Column(String, nullable=True) # 用户IP地址
    port = Column(Integer, nullable=True) # 用户端口号

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

```

## schemas.py
```python
# 导入 Pydantic 的 BaseModel 用于创建数据模型，EmailStr 用于验证邮箱格式
from pydantic import BaseModel, EmailStr,Optional
# 导入 datetime 用于处理时间
from datetime import datetime

# --- 用户相关的 Pydantic 模型 (Schemas) ---

# 用户模型的基础类，包含所有用户共有的字段
class UserBase(BaseModel):
    username: str
    email: EmailStr  # 使用 EmailStr 类型会自动验证邮箱格式

# 创建用户时需要的数据模型，继承自 UserBase
# 在 UserBase 的基础上增加了 password 和 public_key 字段
class UserCreate(UserBase):
    password: str
    public_key: str

# 从数据库读取用户数据并返回给客户端时使用的数据模型
class User(UserBase):
    id: int
    created_at: datetime

    # Pydantic V2的配置，允许模型从ORM对象加载数据
    model_config = {
        "from_attributes": True
    }


# 更新用户数据，允许部分更新
class UserUpdate(BaseModel):
    
    # 更新用户信息时使用的数据模型
    # 所有字段均为可选，允许部分更新
    username: Optional[str] = None        # 可选更新
    email: Optional[EmailStr] = None      # 可选更新，自动验证邮箱格式
    password: Optional[str] = None        # 可选更新
    public_key: Optional[str] = None      # 可选更新
    
    class Config:
        orm_mode = True  # 允许从 ORM 对象读取数据


# 删除用户数据(没有软删字段)
#class UserSoftDelete(BaseModel):
#    pass


# --- 联系人相关的 Pydantic 模型 (Schemas) ---

# 联系人模型的基础类
class ContactBase(BaseModel):
    friend_id: int

# 创建联系人时使用的数据模型
class ContactCreate(ContactBase):
    pass  # 目前没有额外字段，直接继承

# 从数据库读取联系人数据并返回时使用的数据模型
class Contact(ContactBase):
    id: int
    user_id: int
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# --- 消息相关的 Pydantic 模型 (Schemas) ---

# 消息模型的基础类
class MessageBase(BaseModel):
    receiver_id: int
    encrypted_content: str

# 创建消息时使用的数据模型
class MessageCreate(MessageBase):
    pass  # 目前没有额外字段

# 从数据库读取消息数据并返回时使用的数据模型
class Message(MessageBase):
    id: int
    sender_id: int
    sent_at: datetime
    is_read: bool

    model_config = {
        "from_attributes": True
    }


# --- 用于身份认证的 Token 相关模型 ---

# 响应中返回给客户端的 Token 模型
class Token(BaseModel):
    access_token: str
    token_type: str

# 解码后的 Token 中包含的数据模型
class TokenData(BaseModel):
    username: str | None = None  # 用户名，可能为空
```

## server.py
```python
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

# 你可以在这里添加更多的路由器，例如用于认证、消息等
# from .routers import auth_router, messages_router
# app.include_router(auth_router)
# app.include_router(messages_router)
```



