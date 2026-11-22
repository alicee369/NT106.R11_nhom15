from database import get_session
from dependencies import get_current_user_id
from fastapi import APIRouter, Depends
from schemas.base import BaseRequest, BaseResponse, EmptyData
from schemas.reminder import reminderData
from services import reminder_service
from sqlmodel import Session

router = APIRouter(prefix="/api/reminder", tags=["Reminder (UC12)"])


@router.post("/config/get", response_model=BaseResponse[reminderData])
async def get_reminder_config(
    req: BaseRequest[EmptyData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    cfg = reminder_service.get_reminder_config(session, user_id)
    return BaseResponse(
        action="REMINDER_CONFIG_GET",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=reminderData(**cfg),
    )


@router.post("/config/update", response_model=BaseResponse[None])
async def update_reminder_config(
    req: BaseRequest[reminderData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    items = [
        req.data.studyReminder,
        req.data.breakReminder,
        req.data.deadlineReminder,
    ]
    if any(item.notifyBeforeMinutes < 0 for item in items):
        return BaseResponse(
            action="REMINDER_CONFIG_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="REMINDER_INVALID_TIME",
            message="Thời gian báo trước không hợp lệ (không được nhỏ hơn 0).",
            data=None,
        )

    reminder_service.update_reminder_config(
        session=session,
        user_id=user_id,
        config=req.data.model_dump(),
    )
    return BaseResponse(
        action="REMINDER_CONFIG_UPDATE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã lưu cấu hình nhắc nhở.",
        data=None,
    )
