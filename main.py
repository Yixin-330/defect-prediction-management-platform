from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from database import SessionLocal, engine
import models

from git_parser import clone_and_parse_repo
from sqlalchemy import func
import uuid
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
# 允许前端跨域访问（开发阶段配置，生产环境要收紧）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，方便前端本地开发
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)

# 定义“快递单”格式
class StudentCreate(BaseModel):
    name: str
    git_url: str

# 获取数据库连接
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. 查所有学生
@app.get("/students/")
def read_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()

# 2. 新增学生
@app.post("/students/")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = models.Student(name=student.name, git_url=student.git_url)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# 3. 根据 ID 查单个学生
@app.get("/students/{student_id}")
def read_student(student_id: int, db: Session = Depends(get_db)):
    # filter 相当于 SQL 里的 WHERE id = student_id
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if student is None:
        # 如果没找到，返回 404 错误，前端就知道数据不存在
        raise HTTPException(status_code=404, detail="学生不存在")
    return student

# 4. 根据 ID 修改学生信息
@app.put("/students/{student_id}")
def update_student(student_id: int, student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if db_student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 更新数据库里的字段
    db_student.name = student.name
    db_student.git_url = student.git_url
    db.commit()
    db.refresh(db_student)
    return db_student

# 5. 根据 ID 删除学生
@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if db_student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    db.delete(db_student)
    db.commit()
    return {"message": "删除成功"}

# 6. 克隆 Git 仓库并解析提交记录
class RepoCloneRequest(BaseModel):
    repo_url: str

@app.post("/repos/clone")
def clone_repo(request: RepoCloneRequest, db: Session = Depends(get_db)):
    try:
        # 1. 拉取 Git 仓库
        commits_data = clone_and_parse_repo(request.repo_url)
        
        # 2. 检查这个仓库是否已经存过，避免重复
        repo_name = request.repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        existing_repo = db.query(models.Repository).filter(models.Repository.url == request.repo_url).first()
        
        if existing_repo:
            # 如果已经存在，先删掉旧的 commits 记录，重新存（简单粗暴，方便测试）
            db.query(models.Commit).filter(models.Commit.repository_id == existing_repo.id).delete()
            repo = existing_repo
        else:
            # 没存过，新建仓库记录
            repo = models.Repository(
                name=repo_name, 
                url=request.repo_url, 
                cloned_at=datetime.now()
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)
        
        # 3. 把拉取到的 commits 存进数据库
        for c in commits_data:
            db_commit = models.Commit(
                hash=c["hash"],
                author=c["author"],
                email=c["email"],
                message=c["message"],
                date=datetime.fromisoformat(c["date"]),
                repository_id=repo.id
            )
            db.add(db_commit)
        
        db.commit() # 统一提交
        
        return {
            "message": "仓库解析并保存成功",
            "repository_id": repo.id,
            "total_commits_saved": len(commits_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"仓库拉取或保存失败: {str(e)}")

# 7. 查询某个仓库的所有提交记录
@app.get("/repos/{repo_id}/commits")
def read_repo_commits(repo_id: int, db: Session = Depends(get_db)):
    # 先查仓库是否存在
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if repo is None:
        raise HTTPException(status_code=404, detail="仓库不存在")
    
    # 查询该仓库下的所有提交
    commits = db.query(models.Commit).filter(models.Commit.repository_id == repo_id).all()
    return {
        "repository": repo.name,
        "total": len(commits),
        "commits": commits
    }

# 用内存字典临时存任务状态（真实项目应该用 Redis 或数据库）
task_status_db = {}

# 1. 真正在后台执行的耗时任务
def background_clone_and_save(repo_url: str, task_id: str):
    # 因为脱离了请求上下文，必须重新创建一个独立的数据库连接
    db = SessionLocal()
    try:
        # 更新状态为“进行中”
        task_status_db[task_id] = {"status": "processing", "message": "正在克隆并解析仓库..."}
        
        # 执行耗时的 Git 克隆
        commits_data = clone_and_parse_repo(repo_url)
        
        # 存库逻辑（和你之前的一样）
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        existing_repo = db.query(models.Repository).filter(models.Repository.url == repo_url).first()
        
        if existing_repo:
            db.query(models.Commit).filter(models.Commit.repository_id == existing_repo.id).delete()
            repo = existing_repo
        else:
            repo = models.Repository(name=repo_name, url=repo_url, cloned_at=datetime.now())
            db.add(repo)
            db.commit()
            db.refresh(repo)
            
        for c in commits_data:
            db_commit = models.Commit(
                hash=c["hash"], author=c["author"], email=c["email"],
                message=c["message"], date=datetime.fromisoformat(c["date"]),
                repository_id=repo.id
            )
            db.add(db_commit)
        db.commit()
        
        # 更新状态为“成功”
        task_status_db[task_id] = {
            "status": "success", 
            "message": f"解析成功，共保存 {len(commits_data)} 条提交记录",
            "repository_id": repo.id
        }
    except Exception as e:
        task_status_db[task_id] = {"status": "failed", "message": f"仓库拉取失败: {str(e)}"}
    finally:
        db.close()

# 2. 对外提供的异步接口（前端调用这个）
@app.post("/repos/clone-async")
def clone_repo_async(request: RepoCloneRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4()) # 生成唯一任务单号
    # 先把状态设为 pending，然后交给后台执行
    task_status_db[task_id] = {"status": "pending", "message": "任务已提交，正在排队"}
    background_tasks.add_task(background_clone_and_save, request.repo_url, task_id)
    
    return {
        "task_id": task_id,
        "message": "任务已提交后台处理，请通过 /tasks/{task_id} 查询进度"
    }

# 3. 查询任务状态的接口
@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task = task_status_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

# 8. 看板统计接口（供前端画图）
@app.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # 1. 总提交数（真实数据）
    total_commits = db.query(models.Commit).count()
    
    # 2. 总仓库数（真实数据）
    total_repos = db.query(models.Repository).count()
    
    # 3. 总学生数（真实数据）
    total_students = db.query(models.Student).count()

    # 4. 计算高风险数（Mock 规则：暂时把提交信息里包含 "fix" 或 "bug" 的算作高风险）
    # 等 B 同学的模型上线后，这里换成从数据库读预测结果即可
    high_risk_commits = db.query(models.Commit).filter(
        models.Commit.message.ilike("%fix%") | models.Commit.message.ilike("%bug%")
    ).count()

    # 5. 异常提交数（Mock 规则：提交信息小于 5 个字符的算作“低信息提交”）
    abnormal_commits = db.query(models.Commit).filter(
        func.length(models.Commit.message) < 5
    ).count()

    # 6. 最近 5 条提交（供前端展示列表）
    recent_commits = db.query(models.Commit).order_by(models.Commit.date.desc()).limit(5).all()

    # 7. 组装返回数据
    return {
        "total_commits": total_commits,
        "total_repos": total_repos,
        "total_students": total_students,
        "high_risk_commits": high_risk_commits,
        "abnormal_commits": abnormal_commits,
        "recent_commits": recent_commits,
        "risk_trend": [  # 供前端画趋势图的假数据，后续可替换为真实按周统计
            {"date": "2023-11-06", "risk_count": 1},
            {"date": "2023-11-07", "risk_count": 0},
            {"date": "2023-11-08", "risk_count": 2},
            {"date": "2023-11-09", "risk_count": 5}
        ]
    }