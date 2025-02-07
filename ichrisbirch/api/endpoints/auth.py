import json
import logging
from datetime import timedelta
from typing import Annotated
from typing import Optional

import jwt
import pendulum
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch.config import get_settings
from ichrisbirch.database.sqlalchemy.session import get_sqlalchemy_session

settings = get_settings()
logger = logging.getLogger('api.auth')
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f'{settings.api_url}/auth/token/', auto_error=False)


class InvalidCredentialsError(HTTPException):
    def __init__(self, msg: str = 'Could not validate credentials'):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={'WWW-Authenticate': 'Bearer'},
        )


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


def generate_jwt(user_id: str, expires_delta: timedelta = settings.auth.access_token_expire):
    payload = {'sub': user_id, 'iat': pendulum.now(), 'exp': pendulum.now() + expires_delta}
    token = jwt.encode(payload=payload, key=settings.auth.secret_key, algorithm=settings.auth.algorithm)
    return token


def authenticate_with_jwt(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(jwt=token, key=settings.auth.secret_key, algorithms=[settings.auth.algorithm])
        user_id = payload.get('sub')
        if user_id is None:
            logger.warning('user_id missing from jwt')
            return None
    except Exception as e:
        logger.info(f'{e}: token type {type(token)}')
        return None
    logger.info(f'authenticated user with jwt: {user_id}')
    return user_id


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
    auth_headers=Depends(authenticate_with_application_headers),
    auth_jwt=Depends(authenticate_with_jwt),
    auth_oauth2=Depends(authenticate_with_oauth2),
    session=Depends(get_sqlalchemy_session),
):
    logger.debug(f'headers: {auth_headers}')
    logger.debug(f'jwt token: {auth_jwt}')
    logger.debug(f'oauth form: {auth_oauth2}')
    if not (user_id := auth_headers or auth_jwt or auth_oauth2):
        raise InvalidCredentialsError()
    if user := validate_user_id(user_id, session):
        logger.debug(f'validated current user: {user}')
        return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]


def store_refresh_token(user_id: str, refresh_token: str):
    with open('rfrtkns.txt', 'a') as f:
        f.write(f'{user_id}: {refresh_token}\n')


def retrieve_refresh_token(user_id: str) -> str:
    with open('rfrtkns.txt') as f:
        for line in f:
            if line.startswith(user_id):
                return line.split(': ')[1].strip()
    return ''


def delete_refresh_token(user_id: str):
    with open('rfrtkns.txt') as f:
        lines = f.readlines()
    with open('rfrtkns.txt', 'w') as f:
        for line in lines:
            if not line.startswith(user_id):
                f.write(line)


@router.get('/logout/', response_model=None, status_code=status.HTTP_200_OK)
async def logout_user(user: CurrentUser):
    delete_refresh_token(str(user.get_id()))
    return Response(status_code=status.HTTP_200_OK)


@router.post("/token/", response_model=None, status_code=status.HTTP_201_CREATED)
async def access_token(user: CurrentUser):
    access_token = generate_jwt(user.get_id())
    refresh_token = generate_jwt(user.get_id(), expires_delta=settings.auth.refresh_token_expire)
    store_refresh_token(user.get_id(), refresh_token)

    tokens = {'access_token': access_token, 'refresh_token': refresh_token}
    response = Response(content=json.dumps(tokens), status_code=status.HTTP_201_CREATED)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)  # Not "Bearer" prefixed
    return response


@router.get('/token/validate/', status_code=status.HTTP_200_OK)
async def validate_token(cookie_token: str = Cookie(None), header_token: str = Header(None)):
    token = cookie_token or header_token
    if not authenticate_with_jwt(token):
        return InvalidCredentialsError
    return Response(status_code=status.HTTP_200_OK)


@router.post('/token/refresh/', status_code=status.HTTP_200_OK)
async def refresh_token(cookie_token: str = Cookie(None), header_token: str = Header(None)):
    refresh_token = cookie_token or header_token
    if not (user_id := authenticate_with_jwt(refresh_token)):
        return InvalidCredentialsError

    stored_refresh_token = retrieve_refresh_token(user_id)
    if refresh_token != stored_refresh_token:
        return InvalidCredentialsError

    new_access_token = generate_jwt(user_id)
    response = Response(status_code=status.HTTP_200_OK)
    response.set_cookie(key="access_token", value=f"Bearer {new_access_token}", httponly=True)
    return response
