from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB

from src.models import AbstractBase


class ChatHistory(AbstractBase):
    __tablename__ = "chat_histories"

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=False)
    message = Column(JSONB, nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False)
    chat_metadata = Column(JSONB, nullable=True)
    shared_to_public = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.id}"
