from datetime import date
from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from dependencies import get_current_user_id
from schemas.base import BaseRequest, BaseResponse
from schemas.schedule import (
    ScheduleAddData,
    ScheduleDeleteData,
    ScheduleListData,
    ScheduleListResponseData,
    ScheduleUpdateData,
)
from services import schedule_service

router = APIRouter(prefix="/api/schedule", tags=["Schedule (UC4 - UC7)"])


@router.post("/list", response_model=BaseResponse[ScheduleListResponseData])
async def list_schedule_events(
    req: BaseRequest[ScheduleListData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    try:
        start_d = date.fromisoformat(req.data.startDate)
        end_d = date.fromisoformat(req.data.endDate)
        if end_d < start_d:
            raise ValueError()
    except ValueError:
        return BaseResponse(
            action="SCHEDULE_GET_LIST",
            requestId=req.requestId,
            success=False,
            errorCode="EVENT_INVALID_DATA",
            message="Khoảng ngày truy vấn không hợp lệ (định dạng YYYY-MM-DD).",
            data=None,
        )

    events = schedule_service.list_events(
        session=session,
        user_id=user_id,
        start_date=req.data.startDate,
        end_date=req.data.endDate,
    )
    return BaseResponse(
        action="SCHEDULE_GET_LIST",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=ScheduleListResponseData(events=events),
    )


@router.post("/add", response_model=BaseResponse[None])
async def add_schedule_event(
    req: BaseRequest[ScheduleAddData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if not req.data.title.strip() or req.data.endTime <= req.data.startTime:
        return BaseResponse(
            action="SCHEDULE_ADD",
            requestId=req.requestId,
            success=False,
            errorCode="EVENT_INVALID_DATA",
            message="Thời gian hoặc thông tin không hợp lệ.",
            data=None,
        )

    if schedule_service.has_conflict(
        session, user_id, req.data.startTime, req.data.endTime
    ):
        return BaseResponse(
            action="SCHEDULE_ADD",
            requestId=req.requestId,
            success=False,
            errorCode="SCHEDULE_CONFLICT",
            message="Bị trùng lịch với sự kiện khác.",
            data=None,
        )

    schedule_service.create_event(
        session=session,
        user_id=user_id,
        title=req.data.title,
        event_type=req.data.eventType,
        start_time=req.data.startTime,
        end_time=req.data.endTime,
    )
    return BaseResponse(
        action="SCHEDULE_ADD",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã thêm sự kiện thành công.",
        data=None,
    )


@router.post("/update", response_model=BaseResponse[None])
async def update_schedule_event(
    req: BaseRequest[ScheduleUpdateData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if not req.data.title.strip() or req.data.endTime <= req.data.startTime:
        return BaseResponse(
            action="SCHEDULE_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="EVENT_INVALID_DATA",
            message="Thời gian hoặc thông tin không hợp lệ.",
            data=None,
        )

    if schedule_service.has_conflict(
        session,
        user_id,
        req.data.startTime,
        req.data.endTime,
        exclude_event_id=req.data.eventId,
    ):
        return BaseResponse(
            action="SCHEDULE_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="SCHEDULE_CONFLICT",
            message="Bị trùng lịch với sự kiện khác.",
            data=None,
        )

    updated = schedule_service.update_event(
        session=session,
        user_id=user_id,
        event_id=req.data.eventId,
        title=req.data.title,
        event_type=req.data.eventType,
        start_time=req.data.startTime,
        end_time=req.data.endTime,
    )
    if updated is None:
        return BaseResponse(
            action="SCHEDULE_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="EVENT_NOT_FOUND",
            message="Không tìm thấy sự kiện.",
            data=None,
        )

    return BaseResponse(
        action="SCHEDULE_UPDATE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã cập nhật sự kiện.",
        data=None,
    )


@router.post("/delete", response_model=BaseResponse[None])
async def delete_schedule_event(
    req: BaseRequest[ScheduleDeleteData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    deleted = schedule_service.delete_event(session, user_id, req.data.eventId)
    if not deleted:
        return BaseResponse(
            action="SCHEDULE_DELETE",
            requestId=req.requestId,
            success=False,
            errorCode="EVENT_NOT_FOUND",
            message="Không tìm thấy sự kiện.",
            data=None,
        )

    return BaseResponse(
        action="SCHEDULE_DELETE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã xóa sự kiện.",
        data=None,
    )