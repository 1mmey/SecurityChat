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

# 用于安全地对外展示用户公开信息的模型
class UserPublic(BaseModel):
    id: int
    username: str
    is_online: bool

    model_config = {
        "from_attributes": True
    }

# 用于获取用户P2P连接信息的模型
class UserConnectionInfo(BaseModel):
    username: str
    public_key: str
    ip_address: str | None = None
    port: int | None = None

    model_config = {
        "from_attributes": True
    }

# 用于客户端更新连接信息的模型
class ConnectionInfoUpdate(BaseModel):
    port: int


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

# 消息模型的基础类，定义了所有消息共有的字段
class MessageBase(BaseModel):
    # 发送消息时，前端提供接收者的用户名更方便
    recipient_username: str 
    encrypted_content: str

# 创建消息时使用的数据模型
class MessageCreate(MessageBase):
    pass  # 目前没有额外字段

# 从数据库读取消息数据并返回给客户端时使用的数据模型
class Message(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    encrypted_content: str
    sent_at: datetime

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