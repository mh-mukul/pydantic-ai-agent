from sqlalchemy.orm import Session
from fastapi import Depends, Security
from fastapi.security.api_key import APIKeyHeader
from src.exception_handler import APIKeyException

from src.auth.models import ApiKey
from config.database import get_db

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    if api_key is None:
        raise APIKeyException(
            status=401, message="Authorization header missing")

    token = api_key.replace("Bearer ", "")
    api_key_obj = db.query(ApiKey).filter(
        ApiKey.key == token,
        ApiKey.is_active == True,
        ApiKey.is_deleted == False
    ).first()

    if not api_key_obj:
        raise APIKeyException(status=403, message="Invalid API Key")

    return api_key_obj
