from sqlalchemy import Column, Integer, String, DateTime, Boolean

from src.models import AbstractBase


class ApiKey(AbstractBase):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id}"


class User(AbstractBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True, unique=True)
    phone = Column(String(15), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    is_superuser = Column(Boolean(), nullable=False, default=False)

    def __repr__(self):
        return f"{self.name}"


class UserToken(AbstractBase):
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True)
    expires_at = Column(DateTime(timezone=True))
    user_id = Column(Integer)
    jti = Column(String(255), unique=True)
    is_blacklisted = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.id}"
