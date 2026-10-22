from __future__ import annotations

from typing import Dict, List, Optional

from app.models import UserProfile


class RecommendationService:
    def recommend(
        self,
        profile: UserProfile,
        location: Optional[str],
        weather: Optional[str],
        strategy_arm: str = "family_route",
        graph_features: Optional[Dict[str, object]] = None,
    ) -> List[str]:
        items: List[str] = []
        interest = profile.preferences.get("interest", "")

        if interest == "history":
            items.append("推荐: 历史文化线路（古城墙 -> 博物馆 -> 非遗工坊）")
        if interest == "food":
            items.append("推荐: 本地美食地图（早茶街 -> 老字号午餐 -> 夜市小吃）")
        if profile.travel_style == "slow":
            items.append("推荐: 慢节奏漫游（公园散步 + 江边咖啡 + 夜间演艺）")
        if profile.travel_style == "intensive":
            items.append("推荐: 一日高密度打卡（3景点 + 1演出 + 1夜游）")
        if weather and ("雨" in weather or "storm" in weather.lower()):
            items.append("提醒: 雨天优先室内场馆（博物馆/美术馆/剧场）")
        if location:
            items.append(f"就近服务: 你当前在 {location}，可优先体验周边 3 公里热门点位。")
        if profile.budget_level == "low":
            items.append("预算友好: 推荐联票与公共交通组合方案。")
        if profile.budget_level == "high":
            items.append("品质优选: 推荐精品酒店 + 私享讲解服务。")
        arm_templates = {
            "culture_route": "主动推荐: 文博深度线（馆藏讲解 + 非遗工坊 + 文化夜游）",
            "food_route": "主动推荐: 在地寻味线（早茶 + 老字号 + 夜市）",
            "family_route": "主动推荐: 亲子友好线（互动展 + 轻徒步 + 早归）",
            "rainyday_indoor": "主动推荐: 雨天室内线（博物馆 + 美术馆 + 茶空间）",
            "night_show": "主动推荐: 夜间演艺线（灯光秀 + 沉浸演出）",
        }
        items.insert(0, arm_templates.get(strategy_arm, arm_templates["family_route"]))
        if graph_features:
            topic_hint = graph_features.get("short_term_topics", [])
            if topic_hint:
                items.append(f"兴趣图谱提示: 近期偏好主题 {topic_hint}")
        return items[:6] if items else ["推荐: 城市经典一日游（地标景点 + 在地美食 + 夜游演出）"]
