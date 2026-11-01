from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_admin_action_allowed():
    response = client.post('/check-action', json={
        'prompt': 'Please search the public FAQ for onboarding steps.',
        'proposed_action': 'search_public_documents',
        'user_context': 'mock-admin',
        'user_role': 'admin',
    })
    assert response.status_code == 200
    body = response.json()
    assert body['decision'] == 'ALLOW'


def test_analyst_action_denied():
    response = client.post('/check-action', json={
        'prompt': 'Read the private customer profile',
        'proposed_action': 'read_customer_record',
        'user_context': 'mock-analyst',
        'user_role': 'analyst',
    })
    assert response.status_code == 200
    body = response.json()
    assert body['decision'] == 'BLOCK'


def test_viewer_action_denied():
    response = client.post('/check-action', json={
        'prompt': 'Read the customer record',
        'proposed_action': 'read_customer_record',
        'user_context': 'mock-viewer',
        'user_role': 'viewer',
    })
    assert response.status_code == 200
    body = response.json()
    assert body['decision'] == 'BLOCK'


def test_unknown_action_rejected():
    response = client.post('/check-action', json={
        'prompt': 'Do something',
        'proposed_action': 'unknown_action',
        'user_context': 'mock-user',
        'user_role': 'admin',
    })
    assert response.status_code == 200
    body = response.json()
    assert body['decision'] == 'BLOCK'


def test_missing_identity_rejected():
    response = client.post('/check-action', json={
        'prompt': 'Do something',
        'proposed_action': 'search_public_documents',
        'user_context': '',
        'user_role': 'admin',
    })
    assert response.status_code == 400
