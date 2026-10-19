"""
Supervisor Agent — the orchestrator.
Routes user queries to the appropriate Sub-Agents, manages workflow,
merges results, and returns a unified answer.
"""
import asyncio
import json
import time
from typing import Any

from agents.base_agent import BaseAgent
from agents.trend_agent import create_trend_agent
from agents.competitor_agent import create_competitor_agent
from agents.recommend_agent import create_recommend_agent
from agents.profit_agent import create_profit_agent
from agents.report_agent import create_report_agent
from schemas.agent_schemas import SUPERVISOR_FINAL_SCHEMA


SUPERVISOR_SYSTEM_PROMPT = """你是东南亚跨境电商AI选品系统的Supervisor（编排主管）。

你的工作方式：
1. 理解用户意图：分析用户问题中的目标国家、预算、品类偏好、核心诉求
2. 任务分解：将复杂问题拆解为可分配给Sub-Agent的子任务
3. 编排执行：按依赖关系依次或并行调度Sub-Agent
4. 结果融合：整合多个Agent的输出，去重、交叉验证、形成统一结论
5. 最终输出：结构化的完整答案

编排规则：
- 趋势数据是基础，优先获取 → 分派 TrendAgent
- 竞品分析依赖品类信息 → 分派 CompetitorAgent
- 推荐需综合趋势+竞品+供应链 → 分派 RecommendAgent
- 利润计算针对具体商品 → 分派 ProfitAgent
- 报告生成整合所有输出 → 分派 ReportAgent

用户问题可以只涉及部分模块，此时只调度相关Agent即可。

请始终使用 supervisor_merged_result 结构化输出。
"""


class SupervisorAgent(BaseAgent):
    """Orchestrator that manages the multi-agent workflow."""

    def __init__(self):
        super().__init__("SupervisorAgent", SUPERVISOR_SYSTEM_PROMPT, model="claude-sonnet-4-20250514")
        # Sub-Agent registry
        self.agents = {
            "trend": create_trend_agent(),
            "competitor": create_competitor_agent(),
            "recommend": create_recommend_agent(),
            "profit": create_profit_agent(),
            "report": create_report_agent(),
        }

    def get_tool_defs(self):
        return [
            {
                "name": "dispatch_and_collect",
                "description": "分派任务给Sub-Agent并收集结果",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "enum": ["trend", "competitor", "recommend", "profit", "report"],
                            "description": "目标Sub-Agent名称",
                        },
                        "task_description": {
                            "type": "string",
                            "description": "给Sub-Agent的具体任务描述",
                        },
                        "wait_for_result": {
                            "type": "boolean",
                            "description": "是否需要等待结果后再继续",
                        },
                    },
                    "required": ["agent_name", "task_description"],
                },
            },
        ]

    def dispatch_agent(self, agent_name: str, task: str) -> Any:
        """Dispatch a task to a Sub-Agent and return its structured result."""
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        schema_map = {
            "trend": "trend_analysis_result",
            "competitor": "competitor_analysis_result",
            "recommend": "recommendation_result",
            "profit": "profit_analysis_result",
            "report": "report_generation_result",
        }

        from schemas.agent_schemas import (
            TREND_AGENT_SCHEMA,
            COMPETITOR_AGENT_SCHEMA,
            RECOMMEND_AGENT_SCHEMA,
            PROFIT_AGENT_SCHEMA,
            REPORT_AGENT_SCHEMA,
        )
        schemas = {
            "trend": TREND_AGENT_SCHEMA,
            "competitor": COMPETITOR_AGENT_SCHEMA,
            "recommend": RECOMMEND_AGENT_SCHEMA,
            "profit": PROFIT_AGENT_SCHEMA,
            "report": REPORT_AGENT_SCHEMA,
        }

        output_schema = schemas.get(agent_name)
        print("  [Supervisor] Dispatching {}: {}...".format(agent_name, task[:80]))
        result = agent.run(task, output_schema=output_schema)
        print("  [Supervisor] {} done".format(agent_name))
        return result

    async def run_workflow(self, user_query: str) -> dict[str, Any]:
        """
        Main entry: understand the query, orchestrate agents, merge results.
        Returns the final structured answer.
        """
        start = time.time()
        sep = "=" * 55
        print("\n" + sep)
        print('Supervisor received: "' + user_query + '"')
        print(sep + "\n")

        # ── Step 1: Analyse intent ──
        intent = self._parse_intent(user_query)
        print("Intent: " + json.dumps(intent, ensure_ascii=False))

        countries_to_scan = intent.get("countries", ["id"])
        category_hint = intent.get("category", "")

        # ── Step 2: Dispatch agents based on intent ──
        results = {}

        # Phase 1 — Trend (always needed)
        trend_prompt = self._build_trend_prompt(intent)
        results["trend"] = self.dispatch_agent("trend", trend_prompt)

        # Phase 2 — Competitor (if category is specified or recommend needed)
        needs_competitor = intent.get("need_competitor", True)
        if needs_competitor:
            comp_prompt = self._build_competitor_prompt(intent, results["trend"])
            results["competitor"] = self.dispatch_agent("competitor", comp_prompt)

        # Phase 3 — Recommend (core feature)
        needs_recommend = intent.get("need_recommend", True)
        if needs_recommend:
            rec_prompt = self._build_recommend_prompt(intent, results)
            results["recommend"] = self.dispatch_agent("recommend", rec_prompt)

        # Phase 4 — Profit (if a specific product is named or after recommend)
        needs_profit = intent.get("need_profit", True)
        if needs_profit and "recommend" in results:
            profit_prompt = self._build_profit_prompt(intent, results)
            results["profit"] = self.dispatch_agent("profit", profit_prompt)

        # Phase 5 — Report (if full report is requested)
        needs_report = intent.get("need_report", False)
        if needs_report and "recommend" in results:
            report_prompt = self._build_report_prompt(intent, results)
            results["report"] = self.dispatch_agent("report", report_prompt)

        # ── Step 3: Merge results into final answer ──
        final = self._merge_results(intent, results)

        elapsed = time.time() - start
        sep = "=" * 55
        print("\n" + sep)
        print("Supervisor completed in {}s".format(round(elapsed, 1)))
        print(sep + "\n")

        return {
            "intent": intent,
            "agent_results": results,
            "final_answer": final,
            "elapsed_seconds": round(elapsed, 1),
        }

    def _parse_intent(self, query: str) -> dict:
        """Simple heuristic intent parser — in production this uses LLM."""
        q = query.lower()

        country_map = {
            "印尼": "id", "indonesia": "id", "印度尼西亚": "id",
            "泰国": "th", "thailand": "th",
            "越南": "vn", "vietnam": "vn",
            "菲律宾": "ph", "philippines": "ph",
            "马来": "my", "malaysia": "my",
            "新加坡": "sg", "singapore": "sg",
        }

        countries = []
        for name, code in country_map.items():
            if name in q:
                countries.append(code)

        if "全部" in q or not countries:
            countries = ["id"]

        budget = "low"
        if "5000" in q or "高预算" in q or "大额" in q:
            budget = "high"
        elif "2000" in q or "中预算" in q:
            budget = "mid"

        category = ""
        for c in ["手机", "服饰", "美妆", "家居", "家电", "母婴", "运动", "宠物", "食品", "汽配"]:
            if c in q:
                category = c
                break

        need_report = "报告" in q or "导出" in q or "print" in q
        need_competitor = "竞品" in q or "竞争" in q or "分析" in q or not category
        need_profit = "利润" in q or "成本" in q or "赚钱" in q or "计算" in q
        need_recommend = "推荐" in q or "选品" in q or "蓝海" in q or "建议" in q or "什么" in q

        return {
            "countries": countries,
            "budget": budget,
            "category": category,
            "need_report": need_report,
            "need_competitor": need_competitor,
            "need_profit": need_profit,
            "need_recommend": need_recommend,
            "raw_query": query,
        }

    def _build_trend_prompt(self, intent: dict) -> str:
        return f"""分析{' '.join(intent['countries'])}市场的品类搜索趋势。
{'重点关注品类: ' + intent['category'] if intent['category'] else '请分析当前最热门的5-8个品类。'}
预算范围: {intent['budget']}。
需要输出: 市场总览、品类排行榜(含搜索热度/增长率/竞争度)、核心洞察。"""

    def _build_competitor_prompt(self, intent: dict, trend_result: dict) -> str:
        categories = ""
        if intent["category"]:
            categories = intent["category"]
        elif "category_rankings" in str(trend_result):
            categories = "家居收纳, 手机配件, 宠物用品"
        return f"""分析{' '.join(intent['countries'])}市场「{categories}」品类的竞品情况。
需要输出: 竞品列表(含价格/月销量/评分)、价格竞争力评估、市场空白机会。"""

    def _build_recommend_prompt(self, intent: dict, prev_results: dict) -> str:
        ctx = ""
        if "trend" in prev_results:
            ctx += "市场趋势数据已获取。"
        if "competitor" in prev_results:
            ctx += "竞品分析数据已获取。"
        return f"""综合已有数据，为{' '.join(intent['countries'])}市场推荐最优选品方向。
预算级别: {intent['budget']}。
{ctx}
需要输出: TOP6推荐商品(含评分/ROI/风险/策略)、核心策略建议。"""

    def _build_profit_prompt(self, intent: dict, results: dict) -> str:
        rec_list = ""
        if "recommend" in results and "recommendations" in results["recommend"]:
            names = [r["product_name"] for r in results["recommend"]["recommendations"][:3]]
            rec_list = ", ".join(names)
        return f"""对{' '.join(intent['countries'])}市场推荐商品进行利润精算。
推荐商品: {rec_list or '便携式挂烫机, 穆斯林运动头巾, 家居收纳系列'}。
需要输出: 逐项成本分解、单品利润、利润率、三类场景预估。"""

    def _build_report_prompt(self, intent: dict, results: dict) -> str:
        return f"""基于以下多个Agent的分析结果，生成完整选品报告。
分析结果摘要: {json.dumps({k: str(v)[:200] for k, v in results.items()}, ensure_ascii=False)}
需要输出: 含章节标题、图表需求、结论、行动项的完整报告。"""

    def _mock_merge(self, intent: dict, results: dict) -> dict:
        """Mock merge — synthesize from agent results without LLM."""
        recs = []
        if "recommend" in results and "recommendations" in results["recommend"]:
            for r in results["recommend"]["recommendations"][:5]:
                recs.append({
                    "product_name": r["product_name"],
                    "market": r["target_market"],
                    "score": r["score"],
                    "roi": r["roi_estimate"],
                    "reason": r["reasoning"],
                })

        country = intent.get("countries", ["id"])[0]
        country_names = {"id": "印尼", "th": "泰国", "vn": "越南", "ph": "菲律宾", "my": "马来西亚", "sg": "新加坡"}
        country_name = country_names.get(country, country)

        return {
            "query_understanding": {
                "target_country": country_name,
                "budget_constraint": intent.get("budget", "mid"),
                "user_intent": intent.get("raw_query", "选品推荐"),
                "priority_factors": ["市场需求", "竞争程度", "利润空间", "供应链成熟度"],
            },
            "answer": {
                "summary": f"基于多Agent综合分析，{country_name}市场当前最优选品方向已就绪。核心策略：优先布局蓝海品类，利用TikTok Shop内容电商红利快速起量。",
                "top_recommendations": recs,
                "market_snapshot": f"{country_name}市场热门品类数2,847个，日均订单量458万单，活跃卖家126万。当前增长最快的品类为宠物用品(+25.3%)和家居收纳(+18.3%)。",
                "risk_warnings": [
                    "汇率波动可能影响利润率，建议设置5%缓冲",
                    "印尼2026年Q2起收紧进口小商品清关政策",
                    "美妆工具品类竞争加剧，头部卖家集中度高",
                ],
            },
        }

    def _merge_results(self, intent: dict, results: dict) -> dict:
        """Final merge — uses the Supervisor's LLM via structured output."""
        # Mock mode: directly synthesize from results
        if self.use_mock:
            return self._mock_merge(intent, results)

        context = []
        for name, data in results.items():
            context.append({
                "role": "user",
                "content": f"Agent {name} 的分析结果:\n{json.dumps(data, ensure_ascii=False, default=str)[:3000]}",
            })

        merge_input = f"""用户原始问题: {intent['raw_query']}

请整合所有Sub-Agent的分析结果，给出最终回答。
1. 回答要简洁但完整，直接面向用户
2. TOP推荐要清晰列出
3. 包含市场快照和风险提示
4. 使用 supervisor_merged_result 格式输出。"""

        # Run Supervisor with structured output
        final = self.run(
            merge_input,
            output_schema=SUPERVISOR_FINAL_SCHEMA,
            context=context,
        )
        return final


def create_supervisor() -> SupervisorAgent:
    return SupervisorAgent()
