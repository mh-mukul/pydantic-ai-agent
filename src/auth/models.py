from sqlalchemy import Column, Integer, String

from src.models import AbstractBase


class ApiKey(AbstractBase):
    __tablename__ = "api_keys"

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id}"
