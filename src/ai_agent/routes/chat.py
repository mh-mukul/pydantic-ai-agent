import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends

from configs.logger import logger
from configs.database import get_db
from src.helpers import ResponseHelper
from src.auth.dependencies import get_current_user

from src.auth.models import User
from src.ai_agent.models import ChatSession, ChatMessage
from src.ai_agent.schemas import (
    SessionGetResponse,
    SessionListResponse,
    ChatInvoke,
    ChatGetResponse,
    Pagination,
)

from src.ai_agent.utils import (
    AgentDeps,
    fetch_conversation_history,
    save_conversation_history,
    get_new_session
)
from src.ai_agent.core import execute_agent

load_dotenv()
QUADSEARCH_BASE_URL = os.getenv("QUADSEARCH_BASE_URL")
QUADSEARCH_API_KEY = os.getenv("QUADSEARCH_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

router = APIRouter(prefix="/chat", tags=["Chat"])
response = ResponseHelper()


@router.get("")
async def get_sessions(
    request: Request,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = ChatSession.get_active(db).filter(
        ChatSession.user_id == user.id
    )

    # Count total sessions
    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit
    offset = (page - 1) * limit

    # Fetch paginated results
    data_list = (
        query.order_by(ChatSession.date_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    sessions = [SessionGetResponse.model_validate(chat) for chat in data_list]

    base_url = str(request.url.path)
    previous_page_url = f"{base_url}?page={page - 1}&limit={limit}" if page > 1 else None
    next_page_url = f"{base_url}?page={page + 1}&limit={limit}" if page < total_pages else None

    pagination_data = Pagination(
        current_page=page,
        total_pages=total_pages,
        total_records=total_records,
        record_per_page=limit,
        previous_page_url=previous_page_url,
        next_page_url=next_page_url
    )
    resp_data = SessionListResponse(
        sessions=sessions,
        pagination=pagination_data
    )

    return response.success_response(200, "success", data=resp_data)


@router.get("/{session_id}")
async def get_chats(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chats = ChatMessage.get_active(db).filter(
        ChatMessage.session_id == session_id).order_by(ChatMessage.date_time.asc()).all()

    resp_data = [ChatGetResponse.model_validate(chat) for chat in chats]

    return response.success_response(200, "success", data=resp_data)


@router.post("")
async def invoke_agent(
    data: ChatInvoke,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not data.session_id:
        session_id = get_new_session(db=db, user=user)
    else:
        session_id = data.session_id
        if not ChatSession.get_active(db).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user.id
        ).first():
            return response.error_response(404, "Session not found")
    user_message = data.query
    start_time = datetime.now(tz=timezone.utc)

    # Fetch conversation history
    history = await fetch_conversation_history(session_id, db=db)

    # store user's message
    await save_conversation_history(
        session_id=session_id,
        message={"type": "human", "content": user_message},
        date_time=start_time,
        db=db
    )

    # Create agent dependencies
    agent_deps = AgentDeps(
        quadsearch_base_url=QUADSEARCH_BASE_URL,
        quadsearch_api_key=QUADSEARCH_API_KEY,
        collection_name=COLLECTION_NAME
    )

    agent_response = await execute_agent(
        user=user, user_message=user_message, messages=history, agent_deps=agent_deps)
    logger.info(f"Agent response: {agent_response}")

    # Store agent's response
    await save_conversation_history(
        session_id=session_id,
        message={"type": "ai", "content": agent_response},
        date_time=datetime.now(tz=timezone.utc),
        metadata={"duration": (datetime.now(
            tz=timezone.utc) - start_time).total_seconds()},
        db=db
    )
    logger.info(
        f"Chat history saved for session {session_id} and user {user.id}")

    # Return the response
    return response.success_response(200, "Success", data={
        "session_id": session_id,
        "user_id": user.id,
        "response": agent_response,
        "duration": (datetime.now(tz=timezone.utc) - start_time).total_seconds()
    })


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Delete chat session and its messages
    try:
        db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user.id
        ).update(
            {"is_deleted": True, "is_active": False},
            synchronize_session=False
        )

        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).update(
            {"is_deleted": True, "is_active": False},
            synchronize_session=False
        )
        db.commit()
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        db.rollback()
        return response.error_response(500, "Failed to delete session")

    return response.success_response(200, "Session deleted successfully")
