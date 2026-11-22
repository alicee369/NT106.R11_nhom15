from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from dependencies import get_current_user_id
from schemas.base import BaseRequest, BaseResponse, EmptyData
from schemas.pomodoro import (
    MiniPlayerPreferenceData,
    PomodoroResumeResponseData,
    PomodoroSessionIdData,
    PomodoroSettingsData,
    PomodoroStartData,
    PomodoroStartResponseData,
    PomodoroStopResponseData,
)
from services import pomodoro_service

router = APIRouter(prefix="/api/pomodoro", tags=["Pomodoro (UC1 - UC3)"])


@router.post("/start", response_model=BaseResponse[PomodoroStartResponseData])
async def start_pomodoro(
    req: BaseRequest[PomodoroStartData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if req.data.focusMinutes <= 0 or req.data.breakMinutes <= 0:
        return BaseResponse(
            action="POMODORO_START",
            requestId=req.requestId,
            success=False,
            errorCode="POMODORO_INVALID_TIME",
            message="Thời gian học và thời gian nghỉ phải lớn hơn 0.",
            data=None,
        )

    if pomodoro_service.get_active_session(session, user_id) is not None:
        return BaseResponse(
            action="POMODORO_START",
            requestId=req.requestId,
            success=False,
            errorCode="POMODORO_ALREADY_RUNNING",
            message="Đồng hồ đang chạy, không thể bắt đầu phiên mới.",
            data=None,
        )

    result = pomodoro_service.create_session(
        session=session,
        user_id=user_id,
        plan_id=req.data.planId,
        focus_minutes=req.data.focusMinutes,
        break_minutes=req.data.breakMinutes,
    )
    return BaseResponse(
        action="POMODORO_START",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã bắt đầu phiên học Pomodoro.",
        data=PomodoroStartResponseData(**result),
    )


@router.post("/pause", response_model=BaseResponse[None])
async def pause_pomodoro(
    req: BaseRequest[PomodoroSessionIdData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    paused = pomodoro_service.pause_session(session, user_id, req.data.sessionId)
    if paused is None:
        return BaseResponse(
            action="POMODORO_PAUSE",
            requestId=req.requestId,
            success=False,
            errorCode="SESSION_NOT_FOUND",
            message="Không tìm thấy phiên học hoặc phiên không ở trạng thái chạy.",
            data=None,
        )

    return BaseResponse(
        action="POMODORO_PAUSE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã tạm dừng phiên học.",
        data=None,
    )


@router.post("/resume", response_model=BaseResponse[PomodoroResumeResponseData])
async def resume_pomodoro(
    req: BaseRequest[PomodoroSessionIdData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    resumed = pomodoro_service.resume_session(session, user_id, req.data.sessionId)
    if resumed is None:
        return BaseResponse(
            action="POMODORO_RESUME",
            requestId=req.requestId,
            success=False,
            errorCode="SESSION_NOT_FOUND",
            message="Không tìm thấy phiên học hoặc phiên không ở trạng thái tạm dừng.",
            data=None,
        )

    return BaseResponse(
        action="POMODORO_RESUME",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã tiếp tục phiên học.",
        data=PomodoroResumeResponseData(**resumed),
    )


@router.post("/stop", response_model=BaseResponse[PomodoroStopResponseData])
async def stop_pomodoro(
    req: BaseRequest[PomodoroSessionIdData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    stopped = pomodoro_service.stop_session(session, user_id, req.data.sessionId)
    if stopped is None:
        return BaseResponse(
            action="POMODORO_STOP",
            requestId=req.requestId,
            success=False,
            errorCode="SESSION_NOT_FOUND",
            message="Không tìm thấy phiên học đang hoạt động.",
            data=None,
        )

    return BaseResponse(
        action="POMODORO_STOP",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã kết thúc phiên học và lưu thời gian.",
        data=PomodoroStopResponseData(**stopped),
    )


@router.post("/settings/get", response_model=BaseResponse[PomodoroSettingsData])
async def get_pomodoro_settings(
    req: BaseRequest[EmptyData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    settings = pomodoro_service.get_settings(session, user_id)
    return BaseResponse(
        action="POMODORO_SETTINGS_GET",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=PomodoroSettingsData(**settings),
    )


@router.post("/settings/update", response_model=BaseResponse[PomodoroSettingsData])
async def update_pomodoro_settings(
    req: BaseRequest[PomodoroSettingsData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if req.data.focusMinutes <= 0 or req.data.breakMinutes <= 0:
        return BaseResponse(
            action="POMODORO_SETTINGS_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="POMODORO_INVALID_SETTINGS",
            message="Thời gian học và thời gian nghỉ phải lớn hơn 0.",
            data=None,
        )

    saved = pomodoro_service.update_settings(
        session=session,
        user_id=user_id,
        focus_minutes=req.data.focusMinutes,
        break_minutes=req.data.breakMinutes,
    )
    return BaseResponse(
        action="POMODORO_SETTINGS_UPDATE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Cấu hình được lưu.",
        data=PomodoroSettingsData(**saved),
    )


@router.post("/miniplayer/get", response_model=BaseResponse[MiniPlayerPreferenceData])
async def get_miniplayer_preference(
    req: BaseRequest[EmptyData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    is_mini = pomodoro_service.get_miniplayer_preference(session, user_id)
    return BaseResponse(
        action="POMODORO_GET_PREFERENCE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=MiniPlayerPreferenceData(isMiniPlayer=is_mini),
    )


@router.post("/miniplayer/sync", response_model=BaseResponse[None])
async def sync_miniplayer_preference(
    req: BaseRequest[MiniPlayerPreferenceData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    pomodoro_service.sync_miniplayer_preference(session, user_id, req.data.isMiniPlayer)
    return BaseResponse(
        action="POMODORO_SYNC_PREFERENCE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã đồng bộ tùy chọn hiển thị.",
        data=None,
    )