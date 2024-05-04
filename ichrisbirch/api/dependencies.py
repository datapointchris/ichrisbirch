from fastapi import Header
from fastapi import HTTPException

tokens = {'default': 'fake-super-secret', 'jessica': 'jessica-0123'}


async def get_token_header(x_token: str = Header(...)):
    """Get token header."""
    if x_token != tokens.get('default'):
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_query_token(token: str):
    """Get query token."""
    if token != tokens.get('jessica'):
        raise HTTPException(status_code=400, detail="No Jessica token provided")


async def auth():
    """Raise exception if not satisfied."""
    ...
