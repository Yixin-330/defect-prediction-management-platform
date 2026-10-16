from __future__ import annotations

from collections import defaultdict
from typing import List


class SafetyGuardService:
    def __init__(self) -> None:
        self._served_counter = defaultdict(int)

    def evaluate(self, user_id: str, weather: str | None, intent: str) -> List[str]:
        rules: List[str] = []
        self._served_counter[user_id] += 1
        if self._served_counter[user_id] > 3:
            rules.append("high_frequency_suppressed")
        if weather and "雨" in weather:
            rules.append("rainy_preference_indoor")
        if intent == "culture_explore":
            rules.append("evidence_required_culture")
        return rules
