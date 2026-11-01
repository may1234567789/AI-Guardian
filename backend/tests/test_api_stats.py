from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_stats_endpoint_returns_structure():
    response = client.get('/stats')
    assert response.status_code == 200
    body = response.json()
    assert 'total_events' in body
    assert 'decision_distribution' in body
    assert isinstance(body['allowed_requests'], int)
