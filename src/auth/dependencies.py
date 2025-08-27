import jwt
from sqlalchemy.orm import Session
from fastapi import Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from configs.database import get_db
from src.auth.utils import decode_token
from src.auth.exceptions import APIKeyException, JWTException

from src.auth.models import ApiKey, User


# Replace OAuth2PasswordBearer with HTTPBearer for proper Swagger UI display
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    if api_key is None:
        raise APIKeyException(
            status=401, message="Authorization header missing")

    token = api_key.replace("Bearer ", "")
    api_key_obj = ApiKey.get_active(db).filter(
        ApiKey.key == token
    ).first()

    if not api_key_obj:
        raise APIKeyException(status=403, message="Invalid API Key")

    return api_key_obj


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    if credentials is None:
        raise JWTException(401, message="Authorization header missing")

    token = credentials.credentials
    try:
        payload = decode_token(db, token, token_type="access")
        user_id = payload.get('user_id')
        if not user_id:
            raise JWTException(401, message="Invalid token")
    except jwt.PyJWTError:
        raise JWTException(
            401, message="Could not validate credentials")

    user_id = payload.get("user_id")
    user = User.get_active(db).filter(User.id == user_id).first()
    if not user:
        raise JWTException(401, message="Invalid user")
    return user
