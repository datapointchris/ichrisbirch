"""The RFC 9728 metadata `icb auth login <url>` reads before it holds a token.

It names the issuer the CLI logs in through. The CLI refuses the document unless
`resource` matches the URL it was given exactly, so `resource` is the address the
edge serves this API at, which no request can be trusted to say.
"""

from urllib.parse import urlsplit

from fastapi import FastAPI

WELL_KNOWN = '/.well-known/oauth-protected-resource'


def metadata_path(resource: str) -> str:
    """Where the metadata for `resource` is served, as this app sees the path.

    RFC 9728 § 3.1 inserts the well-known suffix between the host and the
    resource's own path, so the API at `https://ichrisbirch.com/api` is described
    at `/.well-known/oauth-protected-resource/api`. That path is outside `/api`,
    so it reaches this app unstripped.
    """
    return WELL_KNOWN + urlsplit(resource).path.rstrip('/')


def add_protected_resource_route(api: FastAPI, resource: str, issuer: str) -> None:
    """Serve the metadata for `resource` without authentication."""
    document: dict[str, object] = {'resource': resource, 'authorization_servers': [issuer]}

    def protected_resource() -> dict[str, object]:
        return document

    api.add_api_route(metadata_path(resource), protected_resource, methods=['GET'], include_in_schema=False)
