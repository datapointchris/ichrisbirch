import pytest
from fastapi import HTTPException

from ichrisbirch.api.dependencies import get_query_token
from ichrisbirch.api.dependencies import get_token_header


@pytest.mark.asyncio
async def test_get_token_header_valid_token():
    """Test get_token_header works with a valid token."""
    token = 'fake-super-secret'
    await get_token_header(token)


@pytest.mark.asyncio
async def test_get_token_header_invalid_token():
    """Test get_token_header raises an error with an invalid token."""
    token = 'invalid-token-name'
    with pytest.raises(HTTPException):
        await get_token_header(x_token=token)


@pytest.mark.asyncio
async def test_get_query_token_valid_token():
    """Test get_query_token works with a valid token."""
    token = 'jessica-0123'
    await get_query_token(token)


@pytest.mark.asyncio
async def test_get_query_token_invalid_token():
    """Test get_query_token raises an error with an invalid token."""
    token = 'invalid-token-name'
    with pytest.raises(HTTPException):
        await get_query_token(token)
