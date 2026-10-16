from __future__ import annotations

from collections import defaultdict
import random
from typing import Dict, List


class BanditPolicyService:
    """Thompson-like bandit with safety constraints for recommendation templates."""

    def __init__(self) -> None:
        self.arms = [
            "culture_route",
            "food_route",
            "family_route",
            "rainyday_indoor",
            "night_show",
        ]
        self.alpha: Dict[str, float] = defaultdict(lambda: 1.0)
        self.beta: Dict[str, float] = defaultdict(lambda: 1.0)
        self.last_user_arm: Dict[str, str] = {}
        self.user_seen: Dict[str, set[str]] = defaultdict(set)

    def choose_arm(self, user_id: str, context: Dict[str, object], variant: str = "treatment") -> str:
        if variant == "control":
            return self._rule_based_default(context)
        candidates = self._filtered_candidates(user_id, context)
        if not candidates:
            candidates = self.arms[:]
        samples = {
            arm: random.betavariate(self.alpha[arm], self.beta[arm])
            for arm in candidates
        }
        selected = max(samples.items(), key=lambda item: item[1])[0]
        self.user_seen[user_id].add(selected)
        self.last_user_arm[user_id] = selected
        return selected

    def reward(self, user_id: str, clicked: int, converted: int, dwell_seconds: int) -> None:
        arm = self.last_user_arm.get(user_id)
        if not arm:
            return
        reward_value = 0.4 * clicked + 0.5 * converted + 0.1 * min(dwell_seconds / 120.0, 1.0)
        self.alpha[arm] += reward_value
        self.beta[arm] += max(0.0, 1.0 - reward_value)

    def _filtered_candidates(self, user_id: str, context: Dict[str, object]) -> List[str]:
        weather = str(context.get("weather", "")).lower()
        guardrails = context.get("guardrails", [])
        candidates = self.arms[:]
        if "rainy_preference_indoor" in guardrails:
            candidates = ["rainyday_indoor", "culture_route"]
        if "high_frequency_suppressed" in guardrails:
            seen = self.user_seen.get(user_id, set())
            candidates = [arm for arm in candidates if arm not in seen]
        if "雨" in weather or "storm" in weather:
            candidates = [arm for arm in candidates if arm != "night_show"]
        return candidates

    def _rule_based_default(self, context: Dict[str, object]) -> str:
        intent = str(context.get("intent", ""))
        if intent == "food_discovery":
            return "food_route"
        if intent == "culture_explore":
            return "culture_route"
        return "family_route"
