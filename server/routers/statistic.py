from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from dependencies import get_current_user_id
from schemas.base import BaseRequest, BaseResponse
from schemas.statistic import (
    StatisticViewRequestData,
    StatisticViewResponseData,
)
from services import statistic_service

router = APIRouter(prefix="/api/statistic", tags=["Statistic (UC16)"])


@router.post("/view", response_model=BaseResponse[StatisticViewResponseData])
async def view_statistic(
    req: BaseRequest[StatisticViewRequestData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    result = statistic_service.get_study_chart(
        session=session,
        user_id=user_id,
        filter_type=req.data.filterType,
        timezone_str=req.data.timezone,
        subject_tag=req.data.subjectTag,
    )
    return BaseResponse(
        action="STATISTIC_GET_CHART",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=StatisticViewResponseData(**result),
    )
