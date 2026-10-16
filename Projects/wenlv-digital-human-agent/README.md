# Wenlv Digital Human Agent (MVP)

面向文旅场景的数字人 Agent 后端 MVP，支持：

- 多轮问答（会话上下文）
- 长文本记忆（按用户持续累积摘要）
- 用户画像（偏好、预算、出行风格）
- 行为数据分析（事件协议 + 特征快照 + 样本导出）
- 混合意图估计（序列特征 + Bayes后验）
- 兴趣动态图谱（用户-主题-POI-时段，时间衰减）
- 主动推荐决策（A/B + Contextual Bandit + 安全约束）
- 文化KG与Graph RAG（证据约束回答，降低文化幻觉）

## 1. 快速启动

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 2. 核心接口

### `POST /api/v1/chat`

请求体示例：

```json
{
  "user_id": "wx_user_001",
  "session_id": "sess_001",
  "message": "我想带孩子去历史文化景点，预算有限",
  "location": "西湖区",
  "weather": "小雨"
}
```

返回包含：

- `answer`: 当前回复
- `memory_summary`: 用户长期记忆摘要
- `profile`: 实时画像标签
- `recommendations`: 个性化推荐列表

### `GET /api/v1/users/{user_id}/profile`
查看用户画像。

### `GET /api/v1/users/{user_id}/recommendations`
按画像 + 查询参数返回推荐项。

### `GET /api/v1/users/{user_id}/analytics`
查看用户行为统计（事件数、主题分布）。

### `POST /api/v1/events`
上报行为事件（点击/停留/反馈），用于在线策略更新。

### `GET /api/v1/users/{user_id}/features?session_id=...`
获取用户特征快照与兴趣图谱特征。

### `GET /api/v1/knowledge/grounded-answer?query=...`
基于文化KG进行Graph RAG证据回答。

### `POST /api/v1/ops/export-training-samples`
导出训练样本到本地 JSON 文件。

### `GET /api/v1/ops/ab-report`
查看A/B指标与回滚守护判断。

## 3. 微信小程序接入建议

- 小程序端通过 `wx.request` 调用 `/api/v1/chat`
- `user_id` 使用 `openid/unionid` 映射后的内部 ID
- 将 `session_id` 设计为“单次会话 ID”，跨会话共享同一 `user_id`

## 4. 推荐事件示例

```json
{
  "user_id": "wx_user_001",
  "session_id": "sess_001",
  "event_type": "feedback",
  "theme": "culture",
  "clicked": 1,
  "converted": 0,
  "dwell_seconds": 75,
  "metadata": {
    "poi_id": "site_old_street"
  }
}
```

## 5. 下一步增强（建议）

- 接入向量数据库（Milvus/pgvector）做真实 RAG
- 将内存存储替换为 Redis + PostgreSQL
- 接入大模型（Qwen/DeepSeek/OpenAI/Azure）做自然语言生成
- 增加主动推荐任务（定时/事件触发）
- 增加运营后台看板（转化、满意度、推荐点击率）
