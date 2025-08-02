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
from src.ai_agent.models import ChatSession
from src.ai_agent.schemas import (
    ChatInvokeRequest,
    ChatTitleRequest,
    ChatGetResponse,
)

from src.ai_agent.utils import (
    AgentDeps,
    fetch_conversation_history,
    save_conversation_history,
    get_new_session
)
from src.ai_agent.core import execute_agent, execute_metadata_agent

load_dotenv()
QUADSEARCH_BASE_URL = os.getenv("QUADSEARCH_BASE_URL")
QUADSEARCH_API_KEY = os.getenv("QUADSEARCH_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

router = APIRouter(prefix="/chat", tags=["Chat"])
response = ResponseHelper()


@router.post("")
async def invoke_agent(
    data: ChatInvokeRequest,
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

    # Create agent dependencies
    agent_deps = AgentDeps(
        quadsearch_base_url=QUADSEARCH_BASE_URL,
        quadsearch_api_key=QUADSEARCH_API_KEY,
        collection_name=COLLECTION_NAME
    )

    agent_response = await execute_agent(
        user=user, user_message=user_message, messages=history, agent_deps=agent_deps)
    logger.info(f"Agent response: {agent_response}")

    chat_message = await save_conversation_history(
        session_id=session_id,
        human_message=user_message,
        ai_message=agent_response,
        date_time=datetime.now(tz=timezone.utc),
        duration=(datetime.now(tz=timezone.utc) - start_time).total_seconds(),
        db=db
    )
    logger.info(
        f"Chat history saved for session {session_id} and user {user.id}")

    # Return the response
    resp_data = ChatGetResponse.model_validate(chat_message)
    return response.success_response(200, "success", data=resp_data)


@router.post("/title")
async def generate_title(
    request: Request,
    data: ChatTitleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not data.user_message:
        return response.error_response(400, "User message is required")
    if not data.session_id:
        return response.error_response(400, "Session ID is required")

    # Check if session exists
    session = ChatSession.get_active(db).filter(
        ChatSession.session_id == data.session_id,
        ChatSession.user_id == user.id
    ).first()
    if not session:
        return response.error_response(404, "Session not found")

    if session.title:
        return response.success_response(200, "Success", data={
            "title": session.title
        })

    title_response = await execute_metadata_agent(user_message=data.user_message)
    logger.info(f"Title agent response: {title_response}")

    # Store the title in the session
    session.title = title_response
    db.add(session)
    db.commit()

    return response.success_response(200, "Success", data={
        "title": title_response
    })
