import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ichrisbirch.api.protected_resource import add_protected_resource_route


@pytest.mark.parametrize(
    ('resource', 'path'),
    [
        ('https://ichrisbirch.com/api', '/.well-known/oauth-protected-resource/api'),
        ('https://api.docker.localhost', '/.well-known/oauth-protected-resource'),
    ],
)
def test_the_metadata_names_the_resource_and_its_issuer_without_a_credential(resource, path):
    api = FastAPI()
    add_protected_resource_route(api, resource, 'https://auth.example.com')

    response = TestClient(api).get(path)

    assert response.status_code == 200
    assert response.json() == {'resource': resource, 'authorization_servers': ['https://auth.example.com']}
