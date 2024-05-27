import logging
from datetime import timedelta
from typing import Annotated
from typing import Optional

import jwt
import pendulum
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


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


def generate_jwt(user_id: str, expires_delta: timedelta = settings.auth.token_expire_minutes):
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
        logger.warning(e)
        return None
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
        if user := validate_user_email(form_data['username'], session):
            if validate_password(user, form_data['password']):
                return user.get_id()
    return None


def get_current_user(
    user_id_headers=Depends(authenticate_with_application_headers),
    user_id_jwt=Depends(authenticate_with_jwt),
    user_id_oauth2=Depends(authenticate_with_oauth2),
    session=Depends(get_sqlalchemy_session),
):
    logger.debug(f'headers: {user_id_headers}')
    logger.debug(f'jwt token: {user_id_jwt}')
    logger.debug(f'oauth form: {user_id_oauth2}')
    if user_id_headers:
        user_id = user_id_headers
    elif user_id_jwt:
        user_id = user_id_jwt
    elif user_id_oauth2:
        user_id = user_id_oauth2
    else:
        raise InvalidCredentialsError()
    if user := validate_user_id(user_id, session):
        logger.debug(f'validated current user: {user}')
        return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]


@router.post("/token/", response_model=Token, status_code=status.HTTP_201_CREATED)
async def access_token(user: CurrentUser) -> Token:
    access_token = generate_jwt(user.get_id())
    logger.info(f'created access token for user: {user.email}')
    return Token(access_token=access_token, token_type="bearer")  # nosec


@router.get('/token/validate/', status_code=status.HTTP_200_OK)
async def validate_token(token: str = Header(...)):
    try:
        authenticate_with_jwt(token)
        return Response(status_code=status.HTTP_200_OK)
    except InvalidCredentialsError:
        raise InvalidCredentialsError('token is not valid')
