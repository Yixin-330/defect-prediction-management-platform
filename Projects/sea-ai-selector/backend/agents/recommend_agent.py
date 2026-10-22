"""
Recommend Agent — AI-powered product recommendation engine.
"""
import random
from agents.base_agent import BaseAgent
from schemas.agent_schemas import RECOMMEND_AGENT_SCHEMA
from tools.data_tools import (
    get_hot_search_categories,
    get_competitor_products,
    search_1688_suppliers,
    get_logistics_cost,
)


RECOMMEND_SYSTEM_PROMPT = """你是东南亚跨境电商智能选品推荐专家（Recommend Agent）。

你的职责：
1. 综合市场趋势、竞品分析和供应链数据，推荐最优选品方向
2. 识别蓝海品类（高需求 + 低竞争 + 供应链成熟）
3. 对每个推荐商品进行评分和ROI预估
4. 给出具体的策略建议

评分体系（满分100）：
- 市场需求 (30分): 搜索热度 + 增长率
- 竞争环境 (25分): 竞品数量 + 头部集中度
- 利润空间 (25分): 毛利率 + ROI
- 供应链 (20分): 1688匹配度 + 物流可行性

可用工具：
- get_hot_search_categories(country, limit) — 获取热搜品类
- get_competitor_products(category, platform, limit) — 搜索竞品
- search_1688_suppliers(keyword) — 搜索1688供应商
- get_logistics_cost(country, weight_kg) — 物流成本估算

请始终使用 recommendation_result 结构化输出。
"""


_MOCK_RECOMMENDATIONS = [
    {"name": "便携式挂烫机", "icon": "👔", "market": "印尼", "reason": "印尼市场搜索量月增180%，竞争度低，供应链成熟(1688均价¥35)，单品利润空间大", "score": 97, "roi": "285%", "risk": "低", "strategy": "蓝海品类", "cost": 42, "profit": 28, "confidence": 0.94},
    {"name": "穆斯林运动头巾", "icon": "🧕", "market": "马来西亚+印尼", "reason": "斋月后运动需求爆发，双市场共振效应明显，差异化设计空间大", "score": 95, "roi": "320%", "risk": "低", "strategy": "差异化策略", "cost": 28, "profit": 25, "confidence": 0.91},
    {"name": "迷你破壁豆浆机", "icon": "🥛", "market": "越南", "reason": "越南健康饮食趋势上升，TikTok Shop种草转化率高，客单价可做高", "score": 93, "roi": "240%", "risk": "中", "strategy": "爆品策略", "cost": 58, "profit": 35, "confidence": 0.87},
    {"name": "磁吸手机支架车用", "icon": "📱", "market": "菲律宾", "reason": "菲律宾汽车保有量上升，平均客单价$3-5，走量型爆款潜力大", "score": 91, "roi": "350%", "risk": "极低", "strategy": "爆品策略", "cost": 8, "profit": 12, "confidence": 0.92},
    {"name": "儿童硅胶餐盘分格", "icon": "🍽️", "market": "新加坡+马来西亚", "reason": "母婴品类持续增长，品质要求高利润空间大，品牌溢价空间充足", "score": 89, "roi": "260%", "risk": "低", "strategy": "利润策略", "cost": 22, "profit": 18, "confidence": 0.85},
    {"name": "可折叠露营椅超轻", "icon": "🏕️", "market": "泰国", "reason": "东南亚户外露营热度飙升(TikTok #camping 10亿+播放)，泰国市场先行", "score": 88, "roi": "210%", "risk": "中", "strategy": "蓝海品类", "cost": 35, "profit": 22, "confidence": 0.82},
]


class RecommendAgent(BaseAgent):
    def __init__(self):
        super().__init__("RecommendAgent", RECOMMEND_SYSTEM_PROMPT)

    def get_tool_defs(self):
        return [
            {
                "name": "get_hot_search_categories",
                "description": "获取指定国家热搜品类",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["country"],
                },
            },
            {
                "name": "get_competitor_products",
                "description": "搜索竞品数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "platform": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                },
            },
            {
                "name": "search_1688_suppliers",
                "description": "在1688搜索供应商和批发价格",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_keyword": {"type": "string"},
                    },
                    "required": ["product_keyword"],
                },
            },
            {
                "name": "get_logistics_cost",
                "description": "估算物流成本",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string"},
                        "weight_kg": {"type": "number"},
                    },
                    "required": ["country"],
                },
            },
        ]

    def _generate_mock_output(self, input_text: str, schema: dict) -> dict:
        shuffled = random.sample(_MOCK_RECOMMENDATIONS, len(_MOCK_RECOMMENDATIONS))
        return {
            "recommendations": [
                {
                    "rank": i + 1,
                    "product_name": r["name"],
                    "icon": r["icon"],
                    "target_market": r["market"],
                    "reasoning": r["reason"],
                    "score": r["score"],
                    "roi_estimate": r["roi"],
                    "risk_level": r["risk"],
                    "strategy_type": r["strategy"],
                    "estimated_cost_cny": r["cost"],
                    "estimated_profit_cny": r["profit"],
                    "confidence": r["confidence"],
                }
                for i, r in enumerate(shuffled)
            ],
            "strategy_advice": {
                "core_strategy": "优先布局蓝海品类（家居收纳、宠物用品），配合TikTok Shop短视频内容种草，在新兴品类建立先发优势",
                "quick_wins": [
                    "便携挂烫机切入印尼，月推广预算$200即可起量",
                    "菲律宾走量型小商品以Shopee免运活动打爆",
                ],
                "risks_to_watch": [
                    "印尼2026年Q2起收紧进口小商品清关政策，注意合规",
                    "越南盾汇率波动可能影响利润率",
                ],
            },
        }


def create_recommend_agent() -> RecommendAgent:
    return RecommendAgent()
