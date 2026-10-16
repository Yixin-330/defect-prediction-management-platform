from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_chat_returns_intent_and_recommendations():
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "u_test_1",
            "session_id": "s_test_1",
            "message": "我想看文物和非遗，顺便规划路线",
            "location": "古城街区",
            "weather": "小雨",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert payload["ab_variant"] in ("control", "treatment")
    assert payload["intent_state"]["primary_intent"] in {
        "culture_explore",
        "route_plan",
        "food_discovery",
        "ticket_service",
        "traffic_guide",
    }
    assert len(payload["recommendations"]) >= 1


def test_events_and_ab_report_pipeline():
    chat_response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "u_test_2",
            "session_id": "s_test_2",
            "message": "推荐个博物馆路线",
        },
    )
    assert chat_response.status_code == 200

    event_response = client.post(
        "/api/v1/events",
        json={
            "user_id": "u_test_2",
            "session_id": "s_test_2",
            "event_type": "feedback",
            "theme": "culture",
            "clicked": 1,
            "converted": 0,
            "dwell_seconds": 80,
            "metadata": {"location": "古城街区"},
        },
    )
    assert event_response.status_code == 200
    assert event_response.json()["status"] == "ok"

    report_response = client.get("/api/v1/ops/ab-report")
    assert report_response.status_code == 200
    payload = report_response.json()
    assert "metrics" in payload
    assert "guardrail" in payload


def test_graph_rag_grounded_answer_has_citations():
    response = client.get(
        "/api/v1/knowledge/grounded-answer",
        params={"query": "请介绍古城街区里的非遗皮影戏"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert isinstance(payload["citations"], list)
    assert len(payload["citations"]) >= 1
