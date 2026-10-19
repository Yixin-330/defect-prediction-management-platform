from __future__ import annotations

from collections import Counter
import math
from typing import Dict, List

from app.models import FeatureSnapshot, IntentState, Turn


class IntentEstimator:
    """MVP hybrid intent estimator: sequence score + Bayesian prior calibration."""

    def __init__(self) -> None:
        self.intent_keywords: Dict[str, List[str]] = {
            "culture_explore": ["文物", "非遗", "历史", "博物馆", "文化"],
            "route_plan": ["路线", "行程", "一天", "两天", "怎么逛"],
            "food_discovery": ["美食", "吃", "小吃", "餐厅"],
            "ticket_service": ["门票", "预约", "开放", "闭馆"],
            "traffic_guide": ["地铁", "公交", "打车", "交通", "怎么去"],
        }
        self.bayes_priors: Dict[str, float] = {
            "culture_explore": 0.24,
            "route_plan": 0.23,
            "food_discovery": 0.2,
            "ticket_service": 0.18,
            "traffic_guide": 0.15,
        }

    def estimate(self, message: str, history: List[Turn], features: FeatureSnapshot) -> IntentState:
        sequence_scores = self._sequence_logits(message, history)
        posterior = self._bayes_calibrate(sequence_scores, features)
        ranked = sorted(posterior.items(), key=lambda item: item[1], reverse=True)
        primary = ranked[0][0]
        secondary = ranked[1][0] if len(ranked) > 1 else primary
        confidence = float(round(ranked[0][1], 4))
        actionability = "high" if confidence >= 0.55 else "medium" if confidence >= 0.35 else "low"
        return IntentState(
            primary_intent=primary,
            secondary_intent=secondary,
            confidence=confidence,
            actionability=actionability,
            priors=self.bayes_priors,
        )

    def _sequence_logits(self, message: str, history: List[Turn]) -> Dict[str, float]:
        text = message + " " + " ".join(t.text for t in history[-3:])
        counter = Counter()
        for intent, keywords in self.intent_keywords.items():
            for kw in keywords:
                if kw in text:
                    counter[intent] += 1
        if not counter:
            return {k: 1.0 for k in self.intent_keywords}
        return {intent: 1.0 + float(counter.get(intent, 0)) for intent in self.intent_keywords}

    def _bayes_calibrate(self, logits: Dict[str, float], features: FeatureSnapshot) -> Dict[str, float]:
        topic_bias = features.topic_distribution or {}
        raw: Dict[str, float] = {}
        for intent, score in logits.items():
            prior = self.bayes_priors.get(intent, 0.1)
            topic_bonus = 1.0
            if intent == "culture_explore":
                topic_bonus += topic_bias.get("culture", 0.0) * 0.5
            if intent == "food_discovery":
                topic_bonus += topic_bias.get("food", 0.0) * 0.5
            if intent == "traffic_guide":
                topic_bonus += topic_bias.get("traffic", 0.0) * 0.5
            raw[intent] = math.exp(score) * prior * topic_bonus
        total = sum(raw.values()) or 1.0
        return {intent: value / total for intent, value in raw.items()}
