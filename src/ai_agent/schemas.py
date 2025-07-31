from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class ChatTitleRequest(BaseModel):
    user_message: str = Field(..., max_length=500)
    session_id: str


class ChatInvokeRequest(BaseModel):
    session_id: str = Field(None, max_length=100)
    query: str = Field(..., max_length=500)


class SessionGetResponse(BaseModel):
    session_id: str = Field(..., max_length=100)
    title: Optional[str] = Field(None, max_length=255)
    user_id: int
    date_time: datetime
    shared_to_public: bool

    @field_validator('date_time', mode='before')
    @classmethod
    def ensure_datetime_has_timezone(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        from_attributes = True


class ChatGetResponse(BaseModel):
    id: int
    session_id: str = Field(..., max_length=100)
    human_message: str
    ai_message: Optional[str] = None
    date_time: datetime
    duration: Optional[float] = None
    positive_feedback: Optional[bool] = None
    negative_feedback: Optional[bool] = None

    @field_validator('date_time', mode='before')
    @classmethod
    def ensure_datetime_has_timezone(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

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
    chats: List[ChatGetResponse]
    pagination: Pagination


class SessionListResponse(BaseModel):
    sessions: List[SessionGetResponse]
    pagination: Pagination

    class Config:
        from_attributes = True
