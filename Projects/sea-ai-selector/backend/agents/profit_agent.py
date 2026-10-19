"""
Profit Agent — detailed profit calculation and scenario analysis.
"""
import random
from agents.base_agent import BaseAgent
from schemas.agent_schemas import PROFIT_AGENT_SCHEMA
from tools.data_tools import get_platform_fees, get_logistics_cost, get_currency_rate


PROFIT_SYSTEM_PROMPT = """你是东南亚跨境电商利润分析专家（Profit Agent）。

你的职责：
1. 对指定商品进行全链路成本核算
2. 采购成本 → 物流 → 平台费用 → 广告 → 退货损耗逐项分解
3. 计算单品利润和利润率
4. 给出乐观/正常/悲观三种场景分析

成本构成：
- 采购成本 (1688批发价)
- 头程物流 (国内→海外仓)
- 尾程物流 (海外仓→消费者)
- 平台佣金 + 支付手续费 + 服务费
- 广告推广费 (按售价百分比)
- 退货损耗率
- 关税 (按品类和国家)

可用工具：
- get_platform_fees(platform, price_cny) — 平台费用计算
- get_logistics_cost(country, weight_kg) — 物流成本
- get_currency_rate(country) — 实时汇率

请始终使用 profit_analysis_result 结构化输出。
"""


class ProfitAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProfitAgent", PROFIT_SYSTEM_PROMPT)

    def get_tool_defs(self):
        return [
            {
                "name": "get_platform_fees",
                "description": "计算平台佣金及各项费用",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "电商平台 shopee/lazada/tokopedia/tiktok"},
                        "price_cny": {"type": "number", "description": "售价(换算人民币)"},
                    },
                    "required": ["platform", "price_cny"],
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
            {
                "name": "get_currency_rate",
                "description": "获取当地货币兑人民币汇率",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string"},
                    },
                    "required": ["country"],
                },
            },
        ]

    def _generate_mock_output(self, input_text: str, schema: dict) -> dict:
        purchase = random.randint(20, 60)
        logistics = random.randint(10, 22)
        price = random.randint(80, 200)
        platform = "shopee"
        country = "id"

        # Extract platform and country from input
        for p in ["shopee", "lazada", "tokopedia", "tiktok"]:
            if p in input_text:
                platform = p
                break
        for c in ["id", "th", "vn", "ph", "my", "sg"]:
            if c in input_text:
                country = c
                break

        fx = get_currency_rate(country)
        fees = get_platform_fees(platform, price)

        total_cost = purchase + logistics + fees["total_fees_cny"] + price * 0.08 + price * 0.03
        profit = price - total_cost
        margin = (profit / price) * 100

        return {
            "cost_breakdown": {
                "purchase_cost_cny": float(purchase),
                "logistics_cny": float(logistics),
                "warehousing_cny": 3.0,
                "platform_commission_cny": fees["commission_cny"],
                "payment_fee_cny": fees["payment_fee_cny"],
                "ad_cost_cny": round(price * 0.08, 2),
                "return_loss_cny": round(price * 0.03, 2),
                "total_cost_cny": round(total_cost, 2),
            },
            "revenue": {
                "selling_price_local": round(price * fx["rate"] / 6.5, 0),
                "selling_price_cny_equiv": float(price),
                "currency": fx["code"],
            },
            "profit_summary": {
                "profit_per_unit_cny": round(profit, 2),
                "profit_margin_pct": round(margin, 1),
                "roi_pct": round((profit / purchase) * 100, 1),
                "health_status": "健康" if margin > 25 else "一般" if margin > 15 else "偏低",
            },
            "scenarios": {
                "optimistic": round(margin + 8, 1),
                "realistic": round(margin, 1),
                "pessimistic": round(margin - 10, 1),
            },
        }


def create_profit_agent() -> ProfitAgent:
    return ProfitAgent()
