import os
import jwt
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from src.auth.exceptions import JWTException

from src.auth.models import UserToken

load_dotenv()

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", 60*24*7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(db: Session, data: dict, jti: str, token_type: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token (access or refresh).

    Args:
        db: Database session (required for refresh tokens)
        data: Data to encode in the token
        jti: JWT ID
        token_type: Type of token ('access' or 'refresh')
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    # Set expiration based on token type
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        if token_type == "access":
            expire = datetime.now(timezone.utc) + \
                timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = datetime.now(timezone.utc) + \
                timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "jti": jti, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Save refresh token to the database
    if token_type == "refresh":
        user_token = UserToken(expires_at=expire,
                               user_id=to_encode.get("user_id"), jti=jti)
        db.add(user_token)
        db.commit()

    return encoded_jwt


def decode_token(db: Session, token: str, token_type: str) -> dict:
    """
    Decode a JWT and validate it.

    Args:
        db: Database session
        token: JWT token to decode
        token_type: Type of token ('access' or 'refresh')

    Returns:
        dict: Decoded token payload
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check token type
        if payload.get("type") != token_type:
            raise JWTException(401, message="Invalid token type")

        # Check if token is blacklisted
        check_blacklist_token(db=db, jti=payload.get("jti"))

        # Additional validation based on token type
        if token_type == "access":
            match_jti_from_db(db=db, jti=payload.get("jti"),
                              user_id=payload.get("user_id"))
        elif token_type == "refresh":
            if not UserToken.get_active(db).filter(
                    UserToken.jti == payload.get("jti")).first():
                raise JWTException(401, message="Invalid token")

        return payload
    except jwt.ExpiredSignatureError:
        raise JWTException(401, message="Token has expired")
    except jwt.InvalidTokenError:
        raise JWTException(401, message="Invalid token")


def blacklist_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise JWTException(
            401, message="Invalid token")
    jti = payload.get("jti")
    check_blacklist_token(db=db, jti=jti)
    db_token = UserToken.get_active(db).filter(
        UserToken.jti == jti, UserToken.is_blacklisted == False).first()
    if db_token:
        db_token.is_blacklisted = True
        db.commit()
    else:
        raise JWTException(401, message="Invalid token")


def check_blacklist_token(db: Session, jti: str):
    db_token = UserToken.get_active(db).filter(
        UserToken.jti == jti, UserToken.is_blacklisted == True).first()
    if db_token:
        raise JWTException(401, message="Token has been blacklisted")
    else:
        return True


def match_jti_from_db(db: Session, jti: str, user_id: int) -> Optional[UserToken]:
    db_token = UserToken.get_active(db).filter(
        UserToken.jti == jti, UserToken.user_id == user_id, UserToken.is_blacklisted == False).first()
    if not db_token:
        raise JWTException(401, message="Invalid token")
    return db_token


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
