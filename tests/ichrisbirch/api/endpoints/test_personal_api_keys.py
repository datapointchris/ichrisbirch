from fastapi import status

from tests.util import show_status_and_response

ENDPOINT = '/api-keys/'


def test_create_personal_api_key(txn_api_logged_in):
    client, session = txn_api_logged_in
    response = client.post(ENDPOINT, json={'name': 'Test Key'})
    assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
    data = response.json()
    assert data['key'].startswith('icb_')
    assert len(data['key']) == 36  # icb_ + 32 hex chars
    assert data['key_prefix'] == data['key'][:8]
    assert data['name'] == 'Test Key'
    assert data['revoked_at'] is None


def test_create_key_returns_key_only_once(txn_api_logged_in):
    client, session = txn_api_logged_in
    create_response = client.post(ENDPOINT, json={'name': 'One-Time Key'})
    assert create_response.status_code == status.HTTP_201_CREATED
    full_key = create_response.json()['key']
    assert full_key.startswith('icb_')

    list_response = client.get(ENDPOINT)
    assert list_response.status_code == status.HTTP_200_OK
    for key in list_response.json():
        assert 'key' not in key or key.get('key') is None
        assert full_key not in str(key)


def test_list_personal_api_keys(txn_api_logged_in):
    client, session = txn_api_logged_in
    client.post(ENDPOINT, json={'name': 'Key A'})
    client.post(ENDPOINT, json={'name': 'Key B'})

    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
    keys = response.json()
    assert len(keys) == 2
    names = {k['name'] for k in keys}
    assert names == {'Key A', 'Key B'}


def test_revoke_personal_api_key(txn_api_logged_in):
    client, session = txn_api_logged_in
    create_response = client.post(ENDPOINT, json={'name': 'Revoke Me'})
    key_id = create_response.json()['id']

    delete_response = client.delete(f'{ENDPOINT}{key_id}/')
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    list_response = client.get(ENDPOINT)
    revoked_key = next(k for k in list_response.json() if k['id'] == key_id)
    assert revoked_key['revoked_at'] is not None


def test_invalid_key_rejected(txn_api):
    """Send an invalid icb_ key as Bearer token and verify 401."""
    client, session = txn_api
    response = client.get('/tasks/', headers={'Authorization': 'Bearer icb_invalidgarbagekeys1234567890'})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_cannot_revoke_other_users_key(txn_multi_client):
    ctx = txn_multi_client
    # Create key as regular user
    create_response = ctx['client_logged_in'].post(ENDPOINT, json={'name': 'My Key'})
    assert create_response.status_code == status.HTTP_201_CREATED
    key_id = create_response.json()['id']

    # Try to revoke as admin (different user) — should 404
    delete_response = ctx['client_admin'].delete(f'{ENDPOINT}{key_id}/')
    assert delete_response.status_code == status.HTTP_404_NOT_FOUND
