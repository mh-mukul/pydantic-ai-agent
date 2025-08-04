from sqlalchemy.orm import Session
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
    ChatGetResponse,
    Pagination,
    ChatFeedbackRequest,
)

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


@router.get("/search")
async def search_sessions(
    request: Request,
    query: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    search_query = f"%{query}%"
    sessions = ChatSession.get_active(db).filter(
        ChatSession.user_id == user.id,
        ChatSession.title.ilike(search_query)
    ).order_by(ChatSession.date_time.desc()).limit(20).all()

    resp_data = [SessionGetResponse.model_validate(chat) for chat in sessions]

    return response.success_response(200, "success", data=resp_data)


@router.get("/session")
async def get_chats(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chats = ChatMessage.get_active(db).filter(
        ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    if not chats:
        return response.error_response(404, "No messages found for this session")

    resp_data = [ChatGetResponse.model_validate(chat) for chat in chats]

    return response.success_response(200, "success", data=resp_data)


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


@router.delete("")
async def delete_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Delete chat session and its messages
    try:
        session = ChatSession.get_active(db).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user.id
        ).first()
        if not session:
            return response.error_response(404, "Session not found")
        session.is_deleted = True
        session.is_active = False
        db.add(session)

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


@router.post("/feedback")
async def submit_feedback(
    request: Request,
    data: ChatFeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        chat = ChatMessage.get_active(db).join(ChatSession).filter(
            ChatMessage.id == data.id,
            ChatSession.user_id == user.id
        ).first()
        if not chat:
            return response.error_response(404, "Chat not found or you don't have access")

        # Update chat feedback
        chat.positive_feedback = data.positive_feedback
        chat.negative_feedback = data.negative_feedback
        db.commit()
    except Exception as e:
        logger.error(f"Error submitting feedback for chat {data.id}: {e}")
        db.rollback()
        return response.error_response(500, "Failed to submit feedback")

    return response.success_response(200, "Feedback submitted successfully")
