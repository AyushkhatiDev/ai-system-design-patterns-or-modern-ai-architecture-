from fastapi.testclient import TestClient
from code_examples.semantic_cache import app

client = TestClient(app)


def test_chat_endpoint_cache_miss():
    """Test that a novel query returns a cache miss and a 200 OK."""
    response = client.post("/api/chat?user_query=What is the capital of France?")
    assert response.status_code == 200

    data = response.json()
    assert "response" in data
    assert data["cache_hit"] is False
