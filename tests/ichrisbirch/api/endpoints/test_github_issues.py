"""Tests for filing a GitHub issue from the app.

Each case runs the real endpoint against a GitHub stand-in served over HTTP, so the request the
endpoint builds, the client call and the translation of GitHub's answer are all exercised rather
than mocked out.
"""

import json
import socket
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi import status
from fastapi.testclient import TestClient

from ichrisbirch.api.endpoints import github_issues
from ichrisbirch.config import get_settings

ISSUE = {'title': 'Chart legend overlaps', 'description': 'The legend covers the last bar.', 'labels': ['bug']}


class GitHubStub:
    """Answers issue creation with a chosen status and keeps the last request it was sent."""

    def __init__(self) -> None:
        self.reply_status = status.HTTP_201_CREATED
        self.received: dict = {}
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802  (BaseHTTPRequestHandler's required spelling)
                length = int(self.headers['Content-Length'])
                stub.received = {'headers': dict(self.headers), 'json': json.loads(self.rfile.read(length))}
                if stub.reply_status == status.HTTP_201_CREATED:
                    body = {'number': 7, 'html_url': 'https://github.test/issues/7', 'title': stub.received['json']['title']}
                else:
                    body = {'message': 'Validation Failed'}
                payload = json.dumps(body).encode()
                self.send_response(stub.reply_status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                """Silence the default stderr access log."""

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_port}/repos/owner/repo/issues'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def shutdown(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture(scope='module')
def github() -> Iterator[GitHubStub]:
    stub = GitHubStub()
    yield stub
    stub.shutdown()


def client_for(issues_url: str) -> TestClient:
    settings = SimpleNamespace(
        github=SimpleNamespace(api_url_issues=issues_url, api_headers={'Authorization': 'Bearer test-token'}),
    )
    app = FastAPI()
    app.include_router(github_issues.router, prefix='/github/issues')
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def closed_port_url() -> str:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    return f'http://127.0.0.1:{port}/repos/owner/repo/issues'


def test_a_created_issue_is_returned_and_github_receives_the_issue(github):
    github.reply_status = status.HTTP_201_CREATED

    response = client_for(github.url).post('/github/issues/', json=ISSUE)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'html_url': 'https://github.test/issues/7', 'number': 7, 'title': ISSUE['title']}
    assert github.received['json']['title'] == ISSUE['title']
    assert github.received['json']['labels'] == ISSUE['labels']
    assert github.received['json']['body'].startswith(ISSUE['description'])
    assert github.received['headers']['Authorization'] == 'Bearer test-token'


def test_a_github_rejection_is_a_failed_dependency_naming_githubs_status(github):
    github.reply_status = status.HTTP_422_UNPROCESSABLE_CONTENT

    response = client_for(github.url).post('/github/issues/', json=ISSUE)

    assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY
    assert response.json() == {'detail': 'GitHub API error: 422'}


def test_an_unreachable_github_is_a_failed_dependency_saying_it_was_not_reached():
    response = client_for(closed_port_url()).post('/github/issues/', json=ISSUE)

    assert response.status_code == status.HTTP_424_FAILED_DEPENDENCY
    assert response.json()['detail'].startswith('Failed to reach GitHub API')
