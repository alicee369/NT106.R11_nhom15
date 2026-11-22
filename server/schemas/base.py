from datetime import datetime, timezone
from typing import Generic, Literal, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

ViewModeType = Literal["DAY", "WEEK", "MONTH"]
EventType = Literal["STUDY", "EXAM", "DEADLINE"]


class EmptyData(BaseModel):
    pass


class BaseRequest(BaseModel, Generic[T]):
    action: str
    requestId: int
    data: T


class BaseResponse(BaseModel, Generic[T]):
    action: str
    requestId: int
    success: bool
    errorCode: Optional[str] = None
    message: str
    data: Optional[T] = None


def utc_now_iso() -> str:
    """Trả về chuỗi thời gian chuẩn ISO 8601 UTC (VD: 2026-11-18T09:30:00Z)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")