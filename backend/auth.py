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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
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