import logging
from typing import Annotated
from typing import Optional

import jwt
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.api.jwt_token_handler import JWTTokenHandler
from ichrisbirch.config import settings
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

logger = logging.getLogger('api.auth')
router = APIRouter()
token_handler = JWTTokenHandler()


def validate_user_email(email: str, session: Session):
    query = select(models.User).where(models.User.email == email)
    if not (user := session.execute(query).scalars().first()):
        logger.warning(f'user with email {email} not found')
    return user


def validate_user_id(user_id: str, session: Session):
    query = select(models.User).where(models.User.alternative_id == user_id)
    if not (user := session.execute(query).scalars().first()):
        logger.warning(f'user with id {user_id} not found')
    return user


def validate_password(user: models.User, password: str):
    if not user.check_password(password):
        logger.warning(f'incorrect password for user: {user.email} ')
        return False
    return True


def get_token_from_header(authorization: Annotated[Optional[str], Header()] = None) -> str | None:
    if authorization is None:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization scheme must be Bearer")
        return token
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization header format")


def authenticate_with_jwt(token: Annotated[str, Depends(get_token_from_header)]) -> str | None:
    try:
        return jwt.decode(jwt=token, key=settings.auth.secret_key, algorithms=[settings.auth.algorithm]).get('sub')
    except Exception as e:
        if 'Invalid token type' not in str(e):
            logger.warning(e)
        return None


def authenticate_with_application_headers(
    x_application_id: Optional[str] = Header(None), x_user_id: Optional[str] = Header(None)
) -> str | None:
    if x_application_id and x_user_id:
        if not x_application_id == settings.flask.app_id:
            logger.warning(f'invalid X-Application-ID header: {x_application_id}')
            return None
        return x_user_id
    return None


async def authenticate_with_oauth2(request: Request, session: Session = Depends(get_sqlalchemy_session)) -> str | None:
    form_data = await request.form()
    if form_data and 'username' in form_data and 'password' in form_data:
        if user := validate_user_email(str(form_data['username']), session):
            if validate_password(user, str(form_data['password'])):
                return user.get_id()
    return None


def get_current_user(
    app_headers=Depends(authenticate_with_application_headers),
    auth_jwt=Depends(authenticate_with_jwt),
    auth_oauth2=Depends(authenticate_with_oauth2),
    session=Depends(get_sqlalchemy_session),
):
    logger.debug(f'app headers: {bool(app_headers)}')
    logger.debug(f'jwt token: {bool(auth_jwt)}')
    logger.debug(f'oauth form: {bool(auth_oauth2)}')
    if not (user_id := app_headers or auth_jwt or auth_oauth2):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    if user := validate_user_id(user_id, session):
        logger.debug(f'validated current user: {user.email}')
        return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]


@router.get('/logout/', response_model=None, status_code=status.HTTP_200_OK)
async def logout_user(x_user_id: str = Header(...)):
    token_handler.delete_refresh_token(x_user_id)
    return Response(status_code=status.HTTP_200_OK)


@router.post('/token/', response_model=None, status_code=status.HTTP_201_CREATED)
async def access_token(response: Response, user: CurrentUser):
    access_token = token_handler.create_access_token(user.get_id())
    refresh_token = token_handler.create_refresh_token(user.get_id())
    token_handler.store_refresh_token(user.get_id(), refresh_token)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': refresh_token}


@router.get('/token/validate/', status_code=status.HTTP_200_OK)
async def validate_token(
    jwt_token: Annotated[str, Depends(get_token_from_header)], access_token: Optional[str] = Cookie(None)
):
    logger.debug(f'token validation - header: {bool(jwt_token)}')
    logger.debug(f'token validation - cookie: {bool(access_token)}')
    token = jwt_token or access_token
    if not token or not authenticate_with_jwt(token):
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={'detail': 'Invalid token'})
    return Response(status_code=status.HTTP_200_OK)


@router.post('/token/refresh/', status_code=status.HTTP_201_CREATED)
async def refresh_token(jwt_token: Annotated[str, Depends(get_token_from_header)], refresh_token: str = Cookie(None)):
    logger.debug(f'token validation - header: {bool(jwt_token)}')
    logger.debug(f'token validation - cookie: {bool(refresh_token)}')
    refresh_token = jwt_token or refresh_token
    if not (user_id := authenticate_with_jwt(refresh_token)):
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={'detail': 'Invalid refresh token'})
    logger.debug(f'refreshing token for user: {user_id}')
    stored_refresh_token = token_handler.retrieve_refresh_token(user_id)
    if refresh_token != stored_refresh_token:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={'detail': 'Invalid refresh token'})
    logger.debug(f'refresh token validated for user: {user_id}')
    new_access_token = token_handler.create_access_token(user_id)
    logger.debug(f'new access token: {new_access_token[-10:]}')
    response = JSONResponse(status_code=status.HTTP_201_CREATED, content={'access_token': new_access_token})
    response.set_cookie(key="access_token", value=f"Bearer {new_access_token}", httponly=True)
    return response
