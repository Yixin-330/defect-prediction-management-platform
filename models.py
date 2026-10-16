from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    git_url = Column(String)

# 新增：仓库表
class Repository(Base):
    __tablename__ = "repositories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    cloned_at = Column(DateTime)
    
    # 建立关系：一个仓库对应多个提交
    commits = relationship("Commit", back_populates="repository")

# 新增：提交记录表
class Commit(Base):
    __tablename__ = "commits"
    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String, index=True)
    author = Column(String)
    email = Column(String)
    message = Column(String)
    date = Column(DateTime)
    
    # 外键，关联到 repositories 表
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    repository = relationship("Repository", back_populates="commits")