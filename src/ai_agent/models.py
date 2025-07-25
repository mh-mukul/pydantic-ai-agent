from sqlalchemy import Column, Integer, String, DateTime, Boolean, cast, func, JSON

from src.models import AbstractBase


class ChatHistory(AbstractBase):
    __tablename__ = "chat_histories"

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=False)
    message = Column(JSON, nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False)
    chat_metadata = Column(JSON, nullable=True)
    shared_to_public = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.id}"


def get_message_type_expr(dialect_name):
    if dialect_name == "postgresql":
        # PostgreSQL JSON text extraction (message ->> 'type')
        return cast(ChatHistory.message.op("->>")("type"), String)
    else:
        # MySQL & SQLite uses json_extract directly
        return func.json_extract(ChatHistory.message, "$.type")
