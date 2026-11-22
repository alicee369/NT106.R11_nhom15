from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from dependencies import get_current_user_id
from schemas.base import BaseRequest, BaseResponse, EmptyData
from schemas.reminder import (
    ReminderConfigData,
    ReminderUpcomingRequestData,
    ReminderUpcomingResponseData,
)
from services import reminder_service

router = APIRouter(prefix="/api/reminder", tags=["Reminder (UC12)"])


@router.post("/config/get", response_model=BaseResponse[ReminderConfigData])
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
        data=ReminderConfigData(**cfg),
    )


@router.post("/config/update", response_model=BaseResponse[None])
async def update_reminder_config(
    req: BaseRequest[ReminderConfigData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    items = [
        req.data.studyReminder,
        req.data.breakReminder,
        req.data.deadlineReminder,
    ]
    if any(item.notifyBeforeMinutes < 0 or item.notifyBeforeMinutes > 10080 for item in items):
        return BaseResponse(
            action="REMINDER_CONFIG_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="REMINDER_INVALID_TIME",
            message="Thời gian báo trước không hợp lệ (chỉ chấp nhận từ 0 đến 10080 phút).",
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


@router.post("/upcoming", response_model=BaseResponse[ReminderUpcomingResponseData])
async def get_upcoming_reminders(
    req: BaseRequest[ReminderUpcomingRequestData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if req.data.windowMinutes is not None and req.data.windowMinutes <= 0:
        return BaseResponse(
            action="REMINDER_GET_UPCOMING",
            requestId=req.requestId,
            success=False,
            errorCode="REMINDER_INVALID_TIME",
            message="Khoảng thời gian quét nhắc nhở phải lớn hơn 0.",
            data=None,
        )

    result = reminder_service.get_upcoming_reminders(
        session=session,
        user_id=user_id,
        window_minutes=req.data.windowMinutes,
        only_due_now=req.data.onlyDueNow,
    )
    return BaseResponse(
        action="REMINDER_GET_UPCOMING",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=ReminderUpcomingResponseData(**result),
    )