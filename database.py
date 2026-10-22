from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 使用 SQLite 数据库，它只是一个文件，非常适合开发阶段
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()