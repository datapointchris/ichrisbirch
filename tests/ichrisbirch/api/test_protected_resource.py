from fastapi import FastAPI
from fastapi.testclient import TestClient

from ichrisbirch.api.protected_resource import add_protected_resource_route


def test_the_metadata_names_the_resource_and_its_issuer_without_a_credential():
    api = FastAPI()
    add_protected_resource_route(api, 'https://ichrisbirch.com', 'https://auth.example.com')

    response = TestClient(api).get('/.well-known/oauth-protected-resource')

    assert response.status_code == 200
    assert response.json() == {'resource': 'https://ichrisbirch.com', 'authorization_servers': ['https://auth.example.com']}
