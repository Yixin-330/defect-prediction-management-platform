"""
Competitor Agent — competitive analysis across SEA platforms.
"""
import random
from agents.base_agent import BaseAgent
from schemas.agent_schemas import COMPETITOR_AGENT_SCHEMA
from tools.data_tools import get_competitor_products, get_price_trend


COMPETITOR_SYSTEM_PROMPT = """你是东南亚跨境电商竞品分析专家（Competitor Agent）。

你的职责：
1. 搜索和分析指定品类/市场的竞品
2. 识别竞品的定价策略和价格变动趋势
3. 分析竞品卖点和销售策略
4. 发现市场空白和差异化机会

分析原则：
- 覆盖Shopee/Lazada/Tokopedia三大平台
- 重点分析月销量高、增长快的竞品
- 识别竞品策略中的弱点和可改进空间
- 给出具体的差异化建议

可用工具：
- get_competitor_products(category, platform, limit) — 搜索竞品
- get_price_trend(product, days) — 获取价格历史趋势

请始终使用 competitor_analysis_result 结构化输出。
"""


class CompetitorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CompetitorAgent", COMPETITOR_SYSTEM_PROMPT)

    def get_tool_defs(self):
        return [
            {
                "name": "get_competitor_products",
                "description": "搜索指定品类或平台的竞品数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "品类关键词"},
                        "platform": {"type": "string", "description": "平台: Shopee/Lazada/Tokopedia"},
                        "limit": {"type": "integer", "description": "返回数量"},
                    },
                },
            },
            {
                "name": "get_price_trend",
                "description": "获取某商品的价格历史趋势",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product": {"type": "string", "description": "商品名"},
                        "days": {"type": "integer", "description": "天数"},
                    },
                    "required": ["product"],
                },
            },
        ]

    def _generate_mock_output(self, input_text: str, schema: dict) -> dict:
        competitors = get_competitor_products(limit=8)
        return {
            "overview": {
                "total_monitored": 1286,
                "new_competitors": 47,
                "price_changes": 23,
                "avg_price_usd": round(sum(c["price"] for c in competitors) / len(competitors), 2),
            },
            "competitors": [
                {
                    "product_name": c["product"],
                    "platform": c["platform"],
                    "price_usd": c["price"],
                    "monthly_sales_est": c["sales"],
                    "rating": c["rating"],
                    "review_count": c.get("reviews", c["sales"] // 2),
                    "price_competitiveness": c["competitiveness"],
                    "key_features": c.get("features", [f"Feature {i}" for i in range(3)]),
                    "selling_strategy": c["strategy"],
                    "strength_score": min(95, int(c["rating"] * 20) - random.randint(0, 5)),
                }
                for c in competitors
            ],
            "niche_opportunities": [
                {"gap_description": "高端功能型家居收纳产品缺乏，市场被低价通用品占据", "market_potential": "high", "entry_difficulty": "easy", "suggested_approach": "推出可定制模块化收纳系统"},
                {"gap_description": "穆斯林女性运动服饰品类空白的差异化空间大", "market_potential": "high", "entry_difficulty": "medium", "suggested_approach": "与本地设计师合作推出联名款"},
            ],
        }


def create_competitor_agent() -> CompetitorAgent:
    return CompetitorAgent()
