import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse

from configs.logger import logger
from configs.database import get_db
from src.helpers import ResponseHelper
from src.auth.dependencies import get_current_user

from src.auth.models import User
from src.ai_agent.models import ChatSession, ChatMessage
from src.ai_agent.schemas import (
    ChatInvokeRequest,
    ChatTitleRequest,
    ChatGetResponse,
    ChatResubmitRequest,
    EditTitleRequest,
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
        chat_session = ChatSession.get_active(db).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user.id
        ).first()
        if not chat_session:
            return response.error_response(404, "Session not found")
        chat_session.date_time = datetime.now(tz=timezone.utc)
        db.add(chat_session)
        db.commit()

    user_message = data.query
    start_time = datetime.now(tz=timezone.utc)
    history = await fetch_conversation_history(session_id=session_id, db=db)

    agent_deps = AgentDeps(
        quadsearch_base_url=QUADSEARCH_BASE_URL,
        quadsearch_api_key=QUADSEARCH_API_KEY,
        collection_name=COLLECTION_NAME
    )

    if data.stream:
        return StreamingResponse(
            await execute_agent(
                user=user,
                user_message=user_message,
                messages=history,
                agent_deps=agent_deps,
                stream=True,
                sse_mode=True,
                session_id=session_id,
                db=db,
                start_time=start_time
            ),
            media_type="text/event-stream"
        )

    else:
        agent_response = await execute_agent(
            user=user,
            user_message=user_message,
            messages=history,
            agent_deps=agent_deps,
            stream=False
        )
        chat_message = await save_conversation_history(
            session_id=session_id,
            human_message=user_message,
            ai_message=agent_response,
            date_time=datetime.now(tz=timezone.utc),
            duration=(datetime.now(tz=timezone.utc) -
                      start_time).total_seconds(),
            db=db
        )
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


@router.post("/edit-title")
async def edit_title(
    request: Request,
    data: EditTitleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        session = ChatSession.get_active(db).filter(
            ChatSession.session_id == data.session_id,
            ChatSession.user_id == user.id
        ).first()
        if not session:
            return response.error_response(404, "Session not found")

        session.title = data.title
        db.commit()
    except Exception as e:
        logger.error(f"Error editing title for session {data.session_id}: {e}")
        db.rollback()
        return response.error_response(500, "Failed to edit title")

    return response.success_response(200, "Title edited successfully")


@router.post("/resubmit")
async def resubmit(
    data: ChatResubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat = ChatMessage.get_active(db).join(ChatSession).filter(
        ChatMessage.id == data.chat_id,
        ChatSession.user_id == user.id
    ).first()
    if not chat:
        return response.error_response(404, "Chat not found or you don't have access")

    chat_session = ChatSession.get_active(db).filter(
        ChatSession.session_id == data.session_id,
        ChatSession.user_id == user.id
    ).first()
    if not chat_session:
        return response.error_response(404, "Session not found or you don't have access")
    chat_session.date_time = datetime.now(tz=timezone.utc)
    db.add(chat_session)
    db.commit()

    user_message = data.query
    start_time = datetime.now(tz=timezone.utc)

    # soft delete all messages after the current chat message for the session
    ChatMessage.get_active(db).filter(
        ChatMessage.session_id == chat.session_id,
        ChatMessage.id > chat.id
    ).update({"is_active": False, "is_deleted": True}, synchronize_session=False)
    db.commit()

    # Fetch conversation history
    history = await fetch_conversation_history(session_id=data.session_id, fetch_until=chat.id, db=db)

    # Create agent dependencies
    agent_deps = AgentDeps(
        quadsearch_base_url=QUADSEARCH_BASE_URL,
        quadsearch_api_key=QUADSEARCH_API_KEY,
        collection_name=COLLECTION_NAME
    )

    if data.stream:
        return StreamingResponse(
            await execute_agent(
                user=user,
                user_message=user_message,
                messages=history,
                agent_deps=agent_deps,
                stream=True,
                sse_mode=True,
                session_id=data.session_id,
                chat=chat,
                db=db,
                start_time=start_time
            ),
            media_type="text/event-stream"
        )
    else:
        agent_response = await execute_agent(
            user=user, user_message=user_message, messages=history, agent_deps=agent_deps)
        logger.info(f"Agent response: {agent_response}")

        chat.human_message = user_message
        chat.ai_message = agent_response
        chat.date_time = datetime.now(tz=timezone.utc)
        chat.duration = (datetime.now(tz=timezone.utc) -
                         start_time).total_seconds()
        chat.positive_feedback = False
        chat.negative_feedback = False

        # Save the updated chat message
        db.add(chat)
        db.commit()
        db.refresh(chat)

        logger.info(
            f"Chat history saved for session {data.session_id} and user {user.id}")

        # Return the response
        resp_data = ChatGetResponse.model_validate(chat)
        return response.success_response(200, "success", data=resp_data)
