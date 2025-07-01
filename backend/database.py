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
# SQLite 是一种文件型数据库，默认状况下，它禁止在多个线程里共享同一个连接
# connect_args={"check_same_thread": False} 是 SQLite 特有的配置，允许在多线程中使用
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建一个数据库会话类 (SessionLocal)
# autocommit=False: 事务不会自动提交
# autoflush=False: 会话不会自动将更改刷新到数据库
# bind=engine: 将会话绑定到我们创建的数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个基础模型类 (Base)，我们定义的 ORM 模型将继承这个类，然后自定义数据表
Base = declarative_base()

# FastAPI 依赖项：获取数据库会话
# 这个函数会在每个请求中创建一个新的数据库会话，并在请求结束后关闭它
def get_db():
    db = SessionLocal()  # 创建会话实例
    try:
        yield db  # 使用 yield 将会话提供给路径操作函数
    finally:
        db.close()  # 确保在请求处理完毕后关闭会话