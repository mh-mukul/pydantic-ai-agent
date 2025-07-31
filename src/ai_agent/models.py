from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Double

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
    human_message = Column(Text, nullable=False)
    ai_message = Column(Text, nullable=True)
    date_time = Column(DateTime(timezone=True), nullable=False)
    duration = Column(Double, nullable=True)  # Duration in seconds
    positive_feedback = Column(Boolean, default=False)
    negative_feedback = Column(Boolean, default=False)

    chat_session = relationship("ChatSession", backref="chat_messages")

    def __repr__(self):
        return f"{self.session_id}"
