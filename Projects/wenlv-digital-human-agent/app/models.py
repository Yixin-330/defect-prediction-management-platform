from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique user id from mini-program openid/unionid.")
    session_id: str = Field(..., description="Conversation session id.")
    message: str = Field(..., min_length=1, description="Current user input.")
    location: Optional[str] = Field(default=None, description="Optional location context.")
    weather: Optional[str] = Field(default=None, description="Optional weather context.")
    step_rate: Optional[float] = Field(default=None, description="Optional steps per minute.")
    facial_emotion: Optional[str] = Field(default=None, description="Optional expression emotion signal.")


class ChatResponse(BaseModel):
    answer: str
    memory_summary: str
    profile: Dict[str, str]
    recommendations: List[str]
    intent_state: Dict[str, object] = Field(default_factory=dict)
    ab_variant: str = "control"
    safety_guardrails: List[str] = Field(default_factory=list)


class Turn(BaseModel):
    role: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    user_id: str
    preferences: Dict[str, str] = Field(default_factory=dict)
    travel_style: str = "balanced"
    budget_level: str = "medium"
    risk_preference: str = "normal"


class AnalyticsEvent(BaseModel):
    user_id: str
    session_id: str
    event_type: str
    metadata: Dict[str, str | float | int] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EventRequest(BaseModel):
    user_id: str
    session_id: str
    event_type: str
    theme: Optional[str] = None
    poi_id: Optional[str] = None
    dwell_seconds: Optional[int] = None
    clicked: Optional[int] = None
    converted: Optional[int] = None
    metadata: Dict[str, str | float | int] = Field(default_factory=dict)


class FeatureSnapshot(BaseModel):
    user_id: str
    topic_distribution: Dict[str, float] = Field(default_factory=dict)
    hour_preference: Dict[str, int] = Field(default_factory=dict)
    geo_hotspots: Dict[str, int] = Field(default_factory=dict)
    session_stage: str = "start"


class IntentState(BaseModel):
    primary_intent: str
    secondary_intent: str
    confidence: float
    actionability: str
    priors: Dict[str, float] = Field(default_factory=dict)
