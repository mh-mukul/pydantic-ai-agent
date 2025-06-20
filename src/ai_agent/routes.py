import os
from dotenv import load_dotenv

from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends

from config.logger import logger
from config.database import get_db
from src.helper import ResponseHelper
from src.auth.dependencies import get_api_key

from src.ai_agent.models import ChatHistory
from src.ai_agent.schemas import (
    ChatInvoke,
    ChatGet,
    Pagination,
    ChatListResponse
)

from src.ai_agent.utils import (
    AgentDeps,
    fetch_conversation_history,
    save_conversation_history
)
from src.ai_agent.core import execute_ebuddy_agent

load_dotenv()
HRIS_BASE_URL = os.getenv("HRIS_BASE_URL")
HRIS_TOKEN = os.getenv("HRIS_TOKEN")
QUADSEARCH_BASE_URL = os.getenv("QUADSEARCH_BASE_URL")
QUADSEARCH_API_KEY = os.getenv("QUADSEARCH_API_KEY")

router = APIRouter(prefix="/chat", tags=["Chat"])
response = ResponseHelper()


@router.get("")
async def get_chats(
    request: Request,
    user_id: int,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: None = Depends(get_api_key)
):
    # Subquery to get the minimum id (first message) per session for the user
    subquery = (
        db.query(func.min(ChatHistory.id).label("min_id"))
        .filter(ChatHistory.user_id == user_id)
        .group_by(ChatHistory.session_id)
        .subquery()
    )

    # Main query: join with subquery to get actual records
    query = db.query(ChatHistory).join(
        subquery, ChatHistory.id == subquery.c.min_id
    )

    # Count total sessions
    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit
    offset = (page - 1) * limit

    # Fetch paginated results
    data_list = (
        query.order_by(ChatHistory.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    chats = [ChatGet.model_validate(chat) for chat in data_list]

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
    resp_data = ChatListResponse(
        chats=chats,
        pagination=pagination_data
    )

    return response.success_response(200, "success", data=resp_data)


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(get_api_key)
):
    chats = ChatHistory.get_active(db).filter(
        ChatHistory.session_id == session_id).order_by(ChatHistory.date_time.asc()).all()

    resp_data = [ChatGet.model_validate(chat) for chat in chats]

    return response.success_response(200, "success", data=resp_data)


@router.post("")
async def invoke_agent(
    data: ChatInvoke,
    request: Request,
    db: Session = Depends(get_db),
    # _: None = Depends(get_api_key)
):
    session_id = data.session_id
    user_id = int(data.user_id)
    user_message = data.query
    start_time = datetime.now()

    # Fetch conversation history
    history = await fetch_conversation_history(session_id, db=db)

    # store user's message
    await save_conversation_history(
        session_id=session_id,
        user_id=user_id,
        message={"type": "human", "content": user_message},
        date_time=start_time,
        db=db
    )

    # Create agent dependencies
    agent_deps = AgentDeps(
        hris_base_url=HRIS_BASE_URL,
        hris_token=HRIS_TOKEN,
        quadsearch_base_url=QUADSEARCH_BASE_URL,
        quadsearch_api_key=QUADSEARCH_API_KEY
    )

    agent_response = await execute_ebuddy_agent(
        user_id=user_id, user_message=user_message, messages=history, agent_deps=agent_deps)
    logger.info(f"Agent response: {agent_response}")

    # Store agent's response
    await save_conversation_history(
        session_id=session_id,
        user_id=user_id,
        message={"type": "ai", "content": agent_response},
        date_time=datetime.now(),
        metadata={"duration": (datetime.now() - start_time).total_seconds()},
        db=db
    )
    logger.info(
        f"Chat history saved for session {session_id} and user {user_id}")

    # Return the response
    return response.success_response(200, "Success", data={
        "session_id": session_id,
        "user_id": user_id,
        "response": agent_response,
        "duration": (datetime.now() - start_time).total_seconds()
    })
