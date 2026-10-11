import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ichrisbirch.api.protected_resource import add_protected_resource_route
from ichrisbirch.api.protected_resource import metadata_path


@pytest.mark.parametrize(
    ('resource', 'path'),
    [
        ('https://ichrisbirch.com/api', '/.well-known/oauth-protected-resource/api'),
        ('https://ichrisbirch.com/api/', '/.well-known/oauth-protected-resource/api'),
        ('https://api.docker.localhost', '/.well-known/oauth-protected-resource'),
    ],
)
def test_the_metadata_path_inserts_the_suffix_before_the_resources_path(resource, path):
    assert metadata_path(resource) == path


def test_the_metadata_names_the_resource_and_its_issuer_without_a_credential():
    api = FastAPI()
    add_protected_resource_route(api, 'https://ichrisbirch.com/api', 'https://auth.example.com')

    response = TestClient(api).get('/.well-known/oauth-protected-resource/api')

    assert response.status_code == 200
    assert response.json() == {'resource': 'https://ichrisbirch.com/api', 'authorization_servers': ['https://auth.example.com']}
