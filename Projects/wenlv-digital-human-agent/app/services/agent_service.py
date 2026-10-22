from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from app.models import AnalyticsEvent, ChatRequest, ChatResponse, Turn
from app.decision.ab_service import ABExperimentService
from app.decision.bandit_policy_service import BanditPolicyService
from app.decision.safety_guard_service import SafetyGuardService
from app.kg.kg_service import CultureKGService
from app.metrics.observability_service import ObservabilityService
from app.models_ml.intent_service import IntentEstimator
from app.pipeline.interest_graph_service import InterestGraphService
from app.rag.graph_rag_service import GraphRAGService
from app.services.analytics_service import AnalyticsService
from app.services.memory_store import MemoryStore
from app.services.profile_service import ProfileService
from app.services.recommendation_service import RecommendationService


class WenlvAgentService:
    def __init__(
        self,
        memory_store: MemoryStore,
        profile_service: ProfileService,
        analytics_service: AnalyticsService,
        recommendation_service: RecommendationService,
    ) -> None:
        self.memory = memory_store
        self.profile = profile_service
        self.analytics = analytics_service
        self.recommendation = recommendation_service
        self.intent_estimator = IntentEstimator()
        self.interest_graph = InterestGraphService()
        self.bandit = BanditPolicyService()
        self.ab = ABExperimentService()
        self.safety = SafetyGuardService()
        self.kg = CultureKGService()
        self.graph_rag = GraphRAGService(self.kg)
        self.metrics = ObservabilityService()
        kb_path = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.json"
        self.kb = json.loads(kb_path.read_text(encoding="utf-8"))

    def chat(self, req: ChatRequest) -> ChatResponse:
        self.memory.add_turn(req.session_id, Turn(role="user", text=req.message))
        user_profile = self.profile.update_from_text(req.user_id, req.message)
        history = self.memory.get_turns(req.session_id)[-6:]
        features = self.analytics.build_feature_snapshot(req.user_id, req.session_id)
        intent_state = self.intent_estimator.estimate(req.message, history, features)
        hour_slot = str(datetime.utcnow().hour)
        theme = self._detect_theme(req.message)
        self.interest_graph.update(req.user_id, theme, None, hour_slot)
        graph_features = self.interest_graph.get_features(req.user_id)
        guardrails = self.safety.evaluate(req.user_id, req.weather, intent_state.primary_intent)
        variant = self.ab.assign_variant(req.user_id)
        selected_arm = self.bandit.choose_arm(
            user_id=req.user_id,
            context={
                "weather": req.weather or "",
                "intent": intent_state.primary_intent,
                "guardrails": guardrails,
            },
            variant=variant,
        )
        answer = self._build_answer(req.message, history, guardrails)
        self.memory.add_turn(req.session_id, Turn(role="assistant", text=answer))
        summary = self.memory.update_summary(req.user_id, req.message, answer)

        recommendations = self.recommendation.recommend(
            profile=user_profile,
            location=req.location,
            weather=req.weather,
            strategy_arm=selected_arm,
            graph_features=graph_features,
        )
        if variant == "control":
            self.metrics.inc("control_impressions")
        else:
            self.metrics.inc("treatment_impressions")
        self.analytics.track(
            AnalyticsEvent(
                user_id=req.user_id,
                session_id=req.session_id,
                event_type="chat",
                metadata={
                    "theme": theme,
                    "location": req.location or "",
                    "ab_variant": variant,
                    "strategy_arm": selected_arm,
                    "intent": intent_state.primary_intent,
                },
            )
        )
        return ChatResponse(
            answer=answer,
            memory_summary=summary,
            profile={
                "travel_style": user_profile.travel_style,
                "budget_level": user_profile.budget_level,
                "risk_preference": user_profile.risk_preference,
                **user_profile.preferences,
            },
            recommendations=recommendations,
            intent_state=intent_state.model_dump(),
            ab_variant=variant,
            safety_guardrails=guardrails,
        )

    def _build_answer(self, message: str, history: List[Turn], guardrails: List[str]) -> str:
        if "evidence_required_culture" in guardrails:
            grounded = self.graph_rag.grounded_answer(message)
            citations = "; ".join(f"{item['node']}<-{item['source']}" for item in grounded["citations"])
            if citations:
                return f"{grounded['answer']}\n\n[证据来源] {citations}"
        matched = None
        for faq in self.kb.get("faqs", []):
            if any(token in message for token in faq["q"].replace("？", "").split()):
                matched = faq["a"]
                break
        if not matched:
            matched = (
                "我可以为你提供文旅行程建议、交通指引、票务与活动推荐。"
                "如果你告诉我出行天数、同行人群和预算，我会给出更精准方案。"
            )
        context = " | ".join([f"{t.role}:{t.text[:30]}" for t in history[-3:]])
        return f"{matched}\n\n[对话上下文] {context}" if context else matched

    def _detect_theme(self, text: str) -> str:
        mapping: Dict[str, str] = {
            "交通": "traffic",
            "地铁": "traffic",
            "门票": "ticket",
            "美食": "food",
            "酒店": "hotel",
            "活动": "event",
            "演出": "event",
            "博物馆": "culture",
        }
        for key, theme in mapping.items():
            if key in text:
                return theme
        return "general"
