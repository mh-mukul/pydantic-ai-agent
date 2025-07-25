from sqlalchemy import Column, Integer, String, DateTime, Boolean, cast, func
from sqlalchemy.ext.hybrid import hybrid_property

from src.models import AbstractBase
from src.custom_types import JSONType


class ChatHistory(AbstractBase):
    __tablename__ = "chat_histories"

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=False)
    message = Column(JSONType, nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False)
    chat_metadata = Column(JSONType, nullable=True)
    shared_to_public = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.id}"


def get_message_type_expr(dialect_name):
    if dialect_name == "postgresql":
        return func.cast(func.jsonb_extract_path_text(ChatHistory.message, "type"), String)
    else:
        return cast(func.json_extract(ChatHistory.message, "$.type"), String)