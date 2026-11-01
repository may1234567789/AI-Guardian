from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_event_list_and_detail():
    scan_response = client.post('/scan', json={'prompt': 'Please summarize the sales report.', 'user_context': 'mock-user'})
    request_id = scan_response.json()['request_id']

    events_response = client.get('/events', params={'limit': 10, 'offset': 0})
    assert events_response.status_code == 200
    assert events_response.json()['count'] >= 1

    detail_response = client.get(f"/events/{request_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()['request_id'] == request_id


def test_missing_event_returns_404():
    response = client.get('/events/does-not-exist')
    assert response.status_code == 404
