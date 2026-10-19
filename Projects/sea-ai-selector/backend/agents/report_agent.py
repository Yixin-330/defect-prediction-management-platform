"""
Report Agent — generates formatted multi-section reports from Agent outputs.
"""
from datetime import datetime
from agents.base_agent import BaseAgent
from schemas.agent_schemas import REPORT_AGENT_SCHEMA


REPORT_SYSTEM_PROMPT = """你是东南亚跨境电商报告生成专家（Report Agent）。

你的职责：
1. 接收其他Agent的输出数据（趋势、竞品、推荐、利润）
2. 整合并生成结构化的专业报告
3. 支持三种报告类型：市场趋势报告、竞品分析报告、AI综合选品报告
4. 报告包含：摘要 → 数据分析 → 洞察发现 → 结论建议 → 行动项

报告质量要求：
- 每个Section要有数据支撑
- 结论清晰可执行
- 包含优先级排序的行动项
- 提示需要哪些图表来辅助说明

可用数据源：
- 由Supervisor通过context传入其他Agent的分析结果
- 无需额外工具调用

请始终使用 report_generation_result 结构化输出。
"""


class ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReportAgent", REPORT_SYSTEM_PROMPT)

    def get_tool_defs(self):
        return []

    def _generate_mock_output(self, input_text: str, schema: dict) -> dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return {
            "report_title": "东南亚跨境电商AI综合选品评估报告",
            "report_type": "AI综合选品报告",
            "generated_at": now,
            "sections": [
                {
                    "section_title": "一、市场总览",
                    "content_markdown": "本期监测到热门品类 **2,847** 个，日均订单量约 **458万** 单。印尼市场GMV占比最高达38%，泰国(22%)和越南(16%)紧随其后。**家居收纳**品类全六国需求上升，竞争度低，为当前最优入场方向。",
                    "charts_needed": [{"chart_type": "pie", "data_source": "gmv_by_country", "description": "各国GMV占比"}],
                },
                {
                    "section_title": "二、竞品分析摘要",
                    "content_markdown": "监控竞品 **1,286** 个，本期新增 **47** 个。手机配件品类价格竞争激烈（月降5.2%），穆斯林服饰品类仍有差异化空间。**核心发现：家居收纳品类头部品牌集中度低，是新卖家最佳切入点。**",
                    "charts_needed": [],
                },
                {
                    "section_title": "三、AI推荐选品TOP3",
                    "content_markdown": "**🥇 便携式挂烫机**（评分97）—— 印尼市场月增180%，竞争度低，ROI 285%\n\n**🥈 穆斯林运动头巾**（评分95）—— 马来+印尼双市场共振，ROI 320%\n\n**🥉 家居收纳系列**（评分96）—— 全六国需求，竞争低，适合走量",
                    "charts_needed": [{"chart_type": "bar", "data_source": "recommendation_scores", "description": "推荐商品综合评分对比"}],
                },
                {
                    "section_title": "四、利润分析",
                    "content_markdown": "首推商品「便携式挂烫机」利润精算：采购成本¥35 + 物流¥15 + 平台费¥8 + 广告¥5 = 总成本¥63。售价换算CNY¥95，**单品利润¥32，利润率33.7%**。乐观场景可达38%，悲观场景约25%。",
                    "charts_needed": [{"chart_type": "bar", "data_source": "cost_breakdown", "description": "成本分解图"}],
                },
            ],
            "conclusion": "当前东南亚市场最佳策略为 **蓝海品类优先（家居收纳/宠物用品）+ TikTok内容种草驱动**。建议首批投入$800-1200，聚焦印尼市场，跑通模型后复制到泰国和马来西亚。",
            "action_items": [
                {"priority": "high", "action": "确定首批选品方向（建议居家收纳或便携挂烫机）", "timeline": "本周"},
                {"priority": "high", "action": "联系1688供应商获取样品，对比3-5家报价", "timeline": "下周"},
                {"priority": "medium", "action": "注册Shopee印尼站卖家账号并完成店铺装修", "timeline": "两周内"},
                {"priority": "medium", "action": "准备3-5条TikTok种草短视频内容素材", "timeline": "三周内"},
                {"priority": "low", "action": "建立汇率监控机制，设置利润率预警线", "timeline": "一个月内"},
            ],
        }


def create_report_agent() -> ReportAgent:
    return ReportAgent()
