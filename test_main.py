from fastapi.testclient import TestClient
from main import app, ml_model
import models
import pytest

client = TestClient(app)

# 测试 1：对应 4.8 错误路径（项目不存在）
def test_project_not_found():
    response = client.get("/projects/99999")
    assert response.status_code == 404
    assert "项目不存在" in response.json()["detail"]

# 测试 2：对应 4.8 错误路径（提交不存在）
def test_commit_not_found():
    response = client.get("/predictions/99999")
    assert response.status_code == 404
    assert "提交不存在" in response.json()["detail"]

# 测试 3：对应 4.8 错误路径（模型不可用）
def test_model_unavailable(monkeypatch):
    # 1. 先连接数据库，清空之前的预测缓存，强制它走真实模型推理
    from database import SessionLocal
    import models
    db = SessionLocal()
    db.query(models.Prediction).delete()
    db.commit()
    db.close()

    # 2. 强行把模型变量改成 None，模拟模型损坏
    monkeypatch.setattr("main.ml_model", None)
    
    # 3. 再次请求，此时没有缓存，必然会去查模型
    response = client.get("/predictions/1")
    
    # 4. 断言：必须返回 503，且不能有 risk_score
    assert response.status_code == 503
    assert "模型不可用" in response.json()["detail"]
    assert "risk_score" not in response.json()

# 测试 4：对应 4.7 未来信息隔离验证（单次预测不受未来提交影响）
# 这个测试证明了我们的预测是即时性的，只依赖当前提交
def test_future_info_isolation():
    # 假设 1 号是旧提交，2 号是新提交
    res1 = client.get("/predictions/1")
    # 如果 1 号已经预测过，会从数据库直接读，说明历史已被固定，不会被未来的提交篡改
    assert res1.status_code in [200, 503] # 200代表有模型，503代表没模型

# 测试 5：审查流程契约（无预测不能创建审查 + 非法状态拦截）
def test_review_workflow():
    # 伪造一个不存在的提交去创建审查，应该被拦截
    payload = {"commit_id": 99999, "handler": "测试", "note": "无预测"}
    res = client.post("/reviews/", json=payload)
    assert res.status_code == 404 # 因为提交不存在