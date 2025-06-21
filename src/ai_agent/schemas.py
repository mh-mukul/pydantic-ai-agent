from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatInvoke(BaseModel):
    session_id: str = Field(None, max_length=100)
    user_id: str = Field(..., max_length=255)
    query: str = Field(..., max_length=500)


class ChatGet(BaseModel):
    id: int
    session_id: str = Field(..., max_length=100)
    user_id: int
    message: dict
    date_time: datetime
    chat_metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    current_page: int
    total_pages: int
    total_records: int
    record_per_page: int
    previous_page_url: Optional[str]
    next_page_url: Optional[str]


class ChatListResponse(BaseModel):
    chats: List[ChatGet]
    pagination: Pagination
