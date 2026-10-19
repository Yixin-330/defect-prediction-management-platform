"""
FastAPI BFF Server — bridges the frontend to the Supervisor + Multi-Agent backend.
Endpoints:
  POST /api/query            — full workflow: user query → Supervisor → Sub-Agents → answer
  POST /api/trend            — Trend Agent only
  POST /api/competitor       — Competitor Agent only
  POST /api/recommend        — Recommend Agent + Profit Agent
  POST /api/profit           — Profit Agent only
  POST /api/report           — Report Agent only
  GET  /api/health           — health check
  GET  /api/workflow-status  — streaming workflow progress (SSE)
"""
import asyncio
import json
import os
import sys
import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.supervisor import create_supervisor
from agents.trend_agent import create_trend_agent
from agents.competitor_agent import create_competitor_agent
from agents.recommend_agent import create_recommend_agent
from agents.profit_agent import create_profit_agent
from agents.report_agent import create_report_agent
from schemas.agent_schemas import (
    TREND_AGENT_SCHEMA,
    COMPETITOR_AGENT_SCHEMA,
    RECOMMEND_AGENT_SCHEMA,
    PROFIT_AGENT_SCHEMA,
    REPORT_AGENT_SCHEMA,
)

app = FastAPI(
    title="SEA AI Selector — Multi-Agent Backend",
    version="3.0.0",
    description="Supervisor + Sub-Agent orchestration for SEA cross-border e-commerce product selection",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Models ──

class QueryRequest(BaseModel):
    query: str
    stream: bool = False

class AgentRequest(BaseModel):
    task: str
    country: str = "id"
    category: str = ""
    budget: str = "mid"
    platform: str = "shopee"

# ── Agent Instances (lazy init) ──

_agents: dict[str, Any] = {}

def get_agent(name: str):
    if name not in _agents:
        factories = {
            "supervisor": create_supervisor,
            "trend": create_trend_agent,
            "competitor": create_competitor_agent,
            "recommend": create_recommend_agent,
            "profit": create_profit_agent,
            "report": create_report_agent,
        }
        if name not in factories:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {name}")
        _agents[name] = factories[name]()
    return _agents[name]


# ── Helper: synchronous agent wrapper ──

def _run_agent(agent_name: str, task: str, schema_key: str | None = None) -> dict:
    """Run a Sub-Agent and return structured result."""
    schemas = {
        "trend": TREND_AGENT_SCHEMA,
        "competitor": COMPETITOR_AGENT_SCHEMA,
        "recommend": RECOMMEND_AGENT_SCHEMA,
        "profit": PROFIT_AGENT_SCHEMA,
        "report": REPORT_AGENT_SCHEMA,
    }
    agent = get_agent(agent_name)
    output_schema = schemas.get(schema_key or agent_name)
    result = agent.run(task, output_schema=output_schema)
    return result


# ── Endpoints ──

@app.get("/api/health")
async def health():
    """Health check — confirms agents are loadable."""
    try:
        sup = get_agent("supervisor")
        agent_count = len(sup.agents)
        return {
            "status": "ok",
            "agents_loaded": agent_count,
            "agents": list(sup.agents.keys()) + ["supervisor"],
            "version": "3.0.0",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def full_query(req: QueryRequest):
    """
    Full workflow: user query → Supervisor → Sub-Agents → merged answer.
    Runs the complete multi-agent pipeline.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    supervisor = get_agent("supervisor")
    try:
        result = await supervisor.run_workflow(req.query)
        return {
            "success": True,
            "intent": result["intent"],
            "answer": result["final_answer"],
            "elapsed_seconds": result["elapsed_seconds"],
            "agent_trace": {
                name: {"status": "completed"} for name in result["agent_results"]
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")


@app.post("/api/query/stream")
async def full_query_stream(req: QueryRequest):
    """
    Streaming version — SSE events as each Agent completes.
    """
    async def event_stream():
        supervisor = get_agent("supervisor")
        yield f"data: {json.dumps({'type': 'status', 'message': '开始分析用户意图...'})}\n\n"
        await asyncio.sleep(0.2)

        # Parse intent (simulate with heuristic + small delay)
        intent = supervisor._parse_intent(req.query)
        yield f"data: {json.dumps({'type': 'intent', 'intent': intent})}\n\n"

        # Phase 1: Trend
        yield f"data: {json.dumps({'type': 'phase', 'phase': 'trend', 'status': 'running'})}\n\n"
        try:
            trend_result = supervisor.dispatch_agent("trend", supervisor._build_trend_prompt(intent))
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'trend', 'status': 'done', 'summary': f'发现{len(trend_result.get("category_rankings",[]))}个热门品类'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'trend', 'status': 'error', 'error': str(e)})}\n\n"
            trend_result = {}

        # Phase 2: Competitor
        yield f"data: {json.dumps({'type': 'phase', 'phase': 'competitor', 'status': 'running'})}\n\n"
        try:
            comp_result = supervisor.dispatch_agent("competitor", supervisor._build_competitor_prompt(intent, trend_result))
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'competitor', 'status': 'done', 'summary': f'分析{len(comp_result.get("competitors",[]))}个竞品'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'competitor', 'status': 'error', 'error': str(e)})}\n\n"
            comp_result = {}

        # Phase 3: Recommend
        yield f"data: {json.dumps({'type': 'phase', 'phase': 'recommend', 'status': 'running'})}\n\n"
        try:
            rec_result = supervisor.dispatch_agent("recommend", supervisor._build_recommend_prompt(intent, {"trend": trend_result, "competitor": comp_result}))
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'recommend', 'status': 'done', 'summary': f'推荐{len(rec_result.get("recommendations",[]))}个商品'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'recommend', 'status': 'error', 'error': str(e)})}\n\n"
            rec_result = {}

        # Phase 4: Profit
        yield f"data: {json.dumps({'type': 'phase', 'phase': 'profit', 'status': 'running'})}\n\n"
        try:
            profit_result = supervisor.dispatch_agent("profit", supervisor._build_profit_prompt(intent, {"recommend": rec_result}))
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'profit', 'status': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'profit', 'status': 'error', 'error': str(e)})}\n\n"
            profit_result = {}

        # Merge
        yield f"data: {json.dumps({'type': 'status', 'message': '正在融合各Agent分析结果...'})}\n\n"
        try:
            final = supervisor._merge_results(intent, {
                "trend": trend_result, "competitor": comp_result,
                "recommend": rec_result, "profit": profit_result,
            })
            yield f"data: {json.dumps({'type': 'complete', 'answer': final, 'elapsed': 0})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/trend")
async def trend_analysis(req: AgentRequest):
    """Run Trend Agent only."""
    task = f"分析{req.country}市场的品类搜索趋势。{f'重点关注品类: {req.category}' if req.category else ''}"
    result = _run_agent("trend", task, "trend")
    return {"success": True, "data": result}


@app.post("/api/competitor")
async def competitor_analysis(req: AgentRequest):
    """Run Competitor Agent only."""
    task = f"分析{req.country}市场「{req.category or '热门品类'}」的竞品情况。"
    result = _run_agent("competitor", task, "competitor")
    return {"success": True, "data": result}


@app.post("/api/recommend")
async def recommend_products(req: AgentRequest):
    """Run Recommend Agent + Profit Agent pipeline."""
    rec_agent = get_agent("recommend")
    profit_agent = get_agent("profit")

    task = f"为{req.country}市场推荐最优选品方向，预算级别: {req.budget}。{f'品类方向: {req.category}' if req.category else ''}"
    rec_result = rec_agent.run(task, output_schema=RECOMMEND_AGENT_SCHEMA)

    # Also run profit on top recommendations
    profit_results = []
    if rec_result and "recommendations" in rec_result:
        for r in rec_result["recommendations"][:3]:
            ptask = f"对商品「{r['product_name']}」在{req.country}市场进行利润精算。"
            try:
                pr = profit_agent.run(ptask, output_schema=PROFIT_AGENT_SCHEMA)
                profit_results.append({"product": r["product_name"], "profit": pr})
            except Exception:
                profit_results.append({"product": r["product_name"], "profit": None})

    return {"success": True, "data": rec_result, "profit_analysis": profit_results}


@app.post("/api/profit")
async def profit_calculation(req: AgentRequest):
    """Run Profit Agent only."""
    task = f"计算指定商品在{req.country}市场的利润。品类: {req.category or '通用'}。平台: {req.platform}。预算: {req.budget}。"
    result = _run_agent("profit", task, "profit")
    return {"success": True, "data": result}


@app.post("/api/report")
async def generate_report(req: AgentRequest):
    """Run Report Agent only (requires context from other agents via the task description)."""
    task = f"""生成一份针对{req.country}市场的跨境电商分析报告。
品类方向: {req.category or '全品类综合分析'}。
报告类型: {'竞品分析报告' if '竞品' in req.task else '市场趋势报告'}。
需要输出完整结构化的报告内容。"""
    result = _run_agent("report", task, "report")
    return {"success": True, "data": result}


# ── Entry Point ──

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    separator = "=" * 55
    print(separator)
    print(" SEA AI Selector - Multi-Agent Backend starting on :{}".format(port))
    print(separator)
    print(" -> Health: http://localhost:{}/api/health".format(port))
    print(" -> POST /api/query  - Full Supervisor workflow")
    print(" -> POST /api/query/stream  - SSE streaming workflow")
    print("")
    print(" Agent pool: supervisor, trend, competitor, recommend, profit, report")
    if os.environ.get("ANTHROPIC_API_KEY"):
        print(" API Key: Set - using REAL Claude API")
    else:
        print(" API Key: NOT SET - using mock mode")
    print(separator)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
