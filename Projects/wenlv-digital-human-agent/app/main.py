from __future__ import annotations

from fastapi import FastAPI

from app.models import ChatRequest, ChatResponse, EventRequest
from app.services.agent_service import WenlvAgentService
from app.services.analytics_service import AnalyticsService
from app.services.memory_store import MemoryStore
from app.services.profile_service import ProfileService
from app.services.recommendation_service import RecommendationService

app = FastAPI(title="Wenlv Digital Human Agent", version="0.1.0")

memory_store = MemoryStore()
profile_service = ProfileService()
analytics_service = AnalyticsService()
recommendation_service = RecommendationService()
agent_service = WenlvAgentService(
    memory_store=memory_store,
    profile_service=profile_service,
    analytics_service=analytics_service,
    recommendation_service=recommendation_service,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return agent_service.chat(req)


@app.get("/api/v1/users/{user_id}/profile")
def get_profile(user_id: str) -> dict:
    profile = profile_service.get_or_create(user_id)
    return profile.model_dump()


@app.get("/api/v1/users/{user_id}/recommendations")
def get_recommendations(user_id: str, location: str | None = None, weather: str | None = None) -> dict:
    profile = profile_service.get_or_create(user_id)
    recommendations = recommendation_service.recommend(profile, location, weather)
    return {"user_id": user_id, "recommendations": recommendations}


@app.get("/api/v1/users/{user_id}/analytics")
def get_analytics(user_id: str) -> dict:
    report = analytics_service.user_report(user_id)
    return {"user_id": user_id, **report}


@app.post("/api/v1/events")
def track_event(req: EventRequest) -> dict:
    analytics_service.track_event_request(req)
    if req.event_type == "feedback":
        agent_service.bandit.reward(
            user_id=req.user_id,
            clicked=int(req.clicked or 0),
            converted=int(req.converted or 0),
            dwell_seconds=int(req.dwell_seconds or 0),
        )
        variant = agent_service.ab.assign_variant(req.user_id)
        key = "ctr_control" if variant == "control" else "ctr_treatment"
        if req.clicked:
            agent_service.metrics.inc(key, 1.0)
    return {"status": "ok"}


@app.get("/api/v1/users/{user_id}/features")
def get_features(user_id: str, session_id: str) -> dict:
    feature = analytics_service.build_feature_snapshot(user_id, session_id)
    graph_features = agent_service.interest_graph.get_features(user_id)
    return {"feature_snapshot": feature.model_dump(), "interest_graph": graph_features}


@app.get("/api/v1/knowledge/grounded-answer")
def grounded_answer(query: str) -> dict:
    return agent_service.graph_rag.grounded_answer(query)


@app.post("/api/v1/ops/export-training-samples")
def export_samples(path: str = "artifacts/training_samples.json") -> dict:
    return analytics_service.export_training_samples(path)


@app.get("/api/v1/ops/ab-report")
def ab_report() -> dict:
    return {
        "metrics": agent_service.metrics.report(),
        "guardrail": agent_service.metrics.online_guardrail(),
    }
