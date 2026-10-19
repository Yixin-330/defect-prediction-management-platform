from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)          # 项目名/团队名
    git_url = Column(String)                    # Git 仓库地址
    owner = Column(String, nullable=True)      # 负责人/团队名（可选）
    description = Column(String, nullable=True) # 项目描述（可选）
    created_at = Column(DateTime, default=datetime.now)

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

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    commit_id = Column(Integer, ForeignKey("commits.id"), unique=True)
    status = Column(String, default="待审查")
    handler = Column(String)
    note = Column(String, nullable=True)
    # 新增：创建时的风险评分（任务 5.5）
    risk_score_at_creation = Column(Float, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    commit_id = Column(Integer, ForeignKey("commits.id"), index=True)
    risk_score = Column(Float)
    level = Column(String)
    model_id = Column(String)
    explanation_available = Column(Integer, default=0)  # 0=不可用, 1=可用
    predicted_at = Column(DateTime, default=datetime.now)