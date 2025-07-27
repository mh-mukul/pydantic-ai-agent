from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends

from configs.logger import logger
from configs.database import get_db
from src.helpers import ResponseHelper
from src.auth.dependencies import get_current_user

from src.auth.models import User
from src.ai_agent.models import ChatSession, ChatMessage
from src.ai_agent.schemas import (
    ChatGetResponse,
)
router = APIRouter(prefix="/chat", tags=["Share"])
response = ResponseHelper()


@router.post("/share/{session_id}")
async def share_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Share chat history for the session
    try:
        chat_history = ChatSession.get_active(db).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user.id
        ).first()

        if not chat_history:
            return response.error_response(404, "Session not found")

        if not chat_history.shared_to_public:
            chat_history.shared_to_public = True
            db.commit()
        else:
            pass  # Already shared, no action needed
    except Exception as e:
        logger.error(f"Error sharing session {session_id}: {e}")
        db.rollback()
        return response.error_response(500, "Failed to share session")

    return response.success_response(200, "Session shared successfully")


@router.get("/share/{session_id}")
async def get_shared_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    # Get shared chat history for the session
    chat_session = ChatSession.get_active(db).filter(
        ChatSession.session_id == session_id,
        ChatSession.shared_to_public == True
    ).first()

    if not chat_session:
        return response.error_response(404, "Session not found or you don't have access")

    chats = ChatMessage.get_active(db).filter(
        ChatMessage.session_id == session_id).order_by(ChatMessage.date_time.asc()).all()

    resp_data = [ChatGetResponse.model_validate(chat) for chat in chats]

    return response.success_response(200, "Session retrieved successfully", data=resp_data)
