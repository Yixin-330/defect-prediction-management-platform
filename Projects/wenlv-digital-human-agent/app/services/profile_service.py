from __future__ import annotations

from typing import Dict

from app.models import UserProfile


class ProfileService:
    def __init__(self) -> None:
        self._profiles: Dict[str, UserProfile] = {}

    def get_or_create(self, user_id: str) -> UserProfile:
        if user_id not in self._profiles:
            self._profiles[user_id] = UserProfile(user_id=user_id)
        return self._profiles[user_id]

    def update_from_text(self, user_id: str, text: str) -> UserProfile:
        profile = self.get_or_create(user_id)
        lowered = text.lower()
        if "亲子" in text:
            profile.preferences["group_type"] = "family"
        if "美食" in text or "吃" in text:
            profile.preferences["interest"] = "food"
        if "历史" in text or "博物馆" in text:
            profile.preferences["interest"] = "history"
        if "省钱" in text or "便宜" in text:
            profile.budget_level = "low"
        if "高端" in text or "品质" in text:
            profile.budget_level = "high"
        if "慢节奏" in text:
            profile.travel_style = "slow"
        elif "特种兵" in text or "打卡" in text:
            profile.travel_style = "intensive"
        if "冒险" in text or "刺激" in text or "night" in lowered:
            profile.risk_preference = "high"
        return profile
