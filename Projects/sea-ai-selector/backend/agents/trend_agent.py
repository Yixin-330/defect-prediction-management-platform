"""
Trend Agent — market trend analysis for SEA e-commerce.
"""
import random
from agents.base_agent import BaseAgent
from schemas.agent_schemas import TREND_AGENT_SCHEMA
from tools.data_tools import get_hot_search_categories, get_market_summary, get_gmv_by_country


TREND_SYSTEM_PROMPT = """你是东南亚跨境电商市场趋势分析师（Trend Agent）。

你的职责：
1. 分析特定国家或全区域的品类搜索热度趋势
2. 识别高增长品类和新兴品类机会
3. 评估各品类的竞争程度
4. 输出结构化市场洞察

分析原则：
- 交叉验证多个数据源（搜索趋势、订单数据、GMV占比）
- 增长率和热度需同时考量，高增长+高热度=重点关注
- 竞争程度要结合卖家数量和市场集中度判断
- 给出可执行的洞察，而非泛泛描述

可用工具：
- get_hot_search_categories(country, limit) — 获取热搜品类
- get_market_summary(country) — 市场总览数据
- get_gmv_by_country() — 各国GMV占比

请始终使用 trend_analysis_result 结构化输出。
"""


_COUNTRY_NAMES = {"id": "印度尼西亚", "th": "泰国", "vn": "越南", "ph": "菲律宾", "my": "马来西亚", "sg": "新加坡"}
_COUNTRY_LIST = ["印尼", "泰国", "越南", "菲律宾", "马来西亚", "新加坡"]
_COMPETITIONS = ["高", "中", "低"]


class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__("TrendAgent", TREND_SYSTEM_PROMPT)

    def get_tool_defs(self):
        return [
            {
                "name": "get_hot_search_categories",
                "description": "获取指定国家电商平台热搜品类榜单",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string", "description": "国家代码: id/th/vn/ph/my/sg"},
                        "limit": {"type": "integer", "description": "返回数量"},
                    },
                    "required": ["country"],
                },
            },
            {
                "name": "get_market_summary",
                "description": "获取指定国家的市场概要数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string", "description": "国家代码"},
                    },
                    "required": ["country"],
                },
            },
            {
                "name": "get_gmv_by_country",
                "description": "获取东南亚各国电商GMV占比",
                "input_schema": {"type": "object", "properties": {}},
            },
        ]

    def _generate_mock_output(self, input_text: str, schema: dict) -> dict:
        """Mock mode: generate trend data from tools directly."""
        # Extract country from input
        country = "id"
        for c in ["id", "th", "vn", "ph", "my", "sg"]:
            if c in input_text or _COUNTRY_NAMES.get(c, "") in input_text:
                country = c
                break

        categories = get_hot_search_categories(country, 8)
        market = get_market_summary(country)
        gmv = get_gmv_by_country()

        return {
            "market_summary": {
                "country": _COUNTRY_NAMES.get(country, country),
                "analysis_date": "2026-06-02",
                "hot_categories_count": len(categories),
                "avg_order_daily_est": market["daily_orders"],
                "avg_ticket_usd": market["avg_ticket"],
            },
            "category_rankings": [
                {
                    "rank": i + 1,
                    "category": c["category"],
                    "icon": c["icon"],
                    "search_heat": c["heat"],
                    "growth_rate_30d": c["growth"],
                    "competition_level": c.get("competition", random.choice(_COMPETITIONS)),
                    "avg_price_usd": c.get("avg_price_usd", round(random.uniform(3, 30), 2)),
                    "main_countries": _COUNTRY_LIST[:random.randint(2, 4)],
                    "recommendation_score": c["score"],
                }
                for i, c in enumerate(categories)
            ],
            "key_findings": [
                {"insight": f"{categories[0]['category']}品类搜索热度最高，月增{categories[0]['growth']}%", "evidence": f"搜素热度指数{categories[0]['heat']}/100", "impact": "high"},
                {"insight": "宠物用品品类月增速最快，达25.3%", "evidence": "近30天搜索量增长趋势", "impact": "high"},
                {"insight": f"{_COUNTRY_NAMES.get(country, country)}市场整体活跃卖家{market['active_sellers']}，同比增长{market['growth_yoy']*100:.0f}%", "evidence": "平台卖家数据", "impact": "medium"},
            ],
        }


# Factory
def create_trend_agent() -> TrendAgent:
    return TrendAgent()
