from uuid import uuid4
from dataclasses import dataclass
from datetime import datetime, timezone
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
from src.auth.models import User
from src.ai_agent.models import ChatSession, ChatMessage


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
        query = ChatMessage.get_active(db)
        data = (
            query
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.date_time.desc())
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
    type: str,
    message: str,
    date_time: datetime = datetime.now(),
    duration: Optional[float] = None,
    db: Session = Depends(get_db)
) -> ChatMessage:
    """Save conversation history to DB."""
    try:
        chat_history = ChatMessage(
            session_id=session_id,
            type=type,
            message=message,
            date_time=date_time,
            duration=duration
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
    messages: List[ChatMessage]
) -> List[Dict[str, Any]]:
    """Convert ChatMessage objects to Pydantic AI ModelMessage format."""
    pydantic_messages = []
    for msg in messages:
        if not msg or not isinstance(msg, ChatMessage):
            logger.warning("Invalid message format or None encountered.")
            continue

        if msg.type == "human":
            pydantic_messages.append(ModelRequest(
                parts=[UserPromptPart(content=msg.message)]))
        else:
            pydantic_messages.append(ModelResponse(
                parts=[TextPart(content=msg.message)]))

    return pydantic_messages


def to_simple_message(
    messages: List[ChatMessage]
) -> List[Dict[str, Any]]:
    """Convert ChatMessage objects to simple message format."""
    simple_messages = []
    for msg in messages:
        if not msg or not isinstance(msg, ChatMessage):
            logger.warning("Invalid message format or None encountered.")
            continue
        simple_messages.append({"type": msg.type, "content": msg.message})
    return simple_messages


def get_new_session(db: Session, user: User) -> str:
    """Create a new session object with a unique session ID."""
    session_id = str(uuid4())
    new_session = ChatSession(
        session_id=session_id, user_id=user.id, date_time=datetime.now(tz=timezone.utc))
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session.session_id
