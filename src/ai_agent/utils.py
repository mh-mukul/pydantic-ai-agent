from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from fastapi import Depends
from sqlalchemy.orm import Session
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart
)

from configs.logger import logger
from configs.database import get_db
from src.ai_agent.models import ChatHistory


# Agent dependencies
@dataclass
class AgentDeps:
    quadsearch_base_url: str
    quadsearch_api_key: str
    collection_name: str


# Fetch conversation between user and AI of a specific session
async def fetch_conversation_history(session_id: str, limit: int = 10, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Fetch conversation history from DB."""
    try:
        query = ChatHistory.get_active(db)
        data = (
            query
            .filter(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.date_time.desc())
            .limit(limit)
            .all()
        )

        # Reverse to get chronological order
        messages = data[::-1]
        return messages
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        return []


# Save conversation history to DB
async def save_conversation_history(
    session_id: str,
    user_id: int,
    message: Dict[str, Any],
    date_time: datetime = datetime.now(),
    metadata: Optional[Dict[str, Any]] = {},
    db: Session = Depends(get_db)
) -> ChatHistory:
    """Save conversation history to DB."""
    try:

        chat_history = ChatHistory(
            session_id=session_id,
            user_id=user_id,
            message=message,
            date_time=date_time,
            chat_metadata=metadata
        )
        db.add(chat_history)
        db.commit()
        db.refresh(chat_history)
        return chat_history
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving conversation history: {e}")
        return None


def to_pydantic_ai_message(
    messages: List[ChatHistory]
) -> List[Dict[str, Any]]:
    """Convert ChatHistory objects to Pydantic AI ModelMessage format."""
    pydantic_messages = []
    for msg in messages:
        if not msg or not isinstance(msg, ChatHistory):
            logger.warning("Invalid message format or None encountered.")
            continue
        msg_data = msg.message
        msg_type = msg_data.get("type")
        msg_content = msg_data.get("content", "")

        if msg_type == "human":
            messages.append(ModelRequest(
                parts=[UserPromptPart(content=msg_content)]))
        else:
            messages.append(ModelResponse(
                parts=[TextPart(content=msg_content)]))
    return pydantic_messages


def to_simple_message(
    messages: List[ChatHistory]
) -> List[Dict[str, Any]]:
    """Convert ChatHistory objects to simple message format."""
    simple_messages = []
    for msg in messages:
        if not msg or not isinstance(msg, ChatHistory):
            logger.warning("Invalid message format or None encountered.")
            continue
        msg_data = msg.message
        msg_type = msg_data.get("type")
        msg_content = msg_data.get("content", "")
        simple_messages.append({"type": msg_type, "content": msg_content})
    return simple_messages


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid4())
