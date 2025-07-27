from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean, cast, func, JSON, ForeignKey

from src.models import AbstractBase


class ChatSession(AbstractBase):
    __tablename__ = "chat_sessions"

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=True)
    user_id = Column(Integer, nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False)
    shared_to_public = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.session_id}"


class ChatMessage(AbstractBase):
    __tablename__ = "chat_messages"

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey(
        'chat_sessions.session_id'), nullable=False, index=True)
    message = Column(JSON, nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False)
    chat_metadata = Column(JSON, nullable=True)

    chat_session = relationship("ChatSession", backref="chat_messages")

    def __repr__(self):
        return f"{self.session_id}"


def get_message_type_expr(dialect_name):
    if dialect_name == "postgresql":
        # PostgreSQL JSON text extraction (message ->> 'type')
        return cast(ChatMessage.message.op("->>")("type"), String)
    else:
        # MySQL & SQLite uses json_extract directly
        return func.json_extract(ChatMessage.message, "$.type")
