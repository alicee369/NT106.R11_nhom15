from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from dependencies import get_current_user_id
from schemas.base import BaseRequest, BaseResponse, EmptyData
from schemas.plan import (
    PlanCreateRequestData,
    PlanDeleteRequestData,
    PlanItem,
    PlanListResponseData,
    PlanUpdateRequestData,
)
from services import plan_service

router = APIRouter(prefix="/api/plan", tags=["Study Plan (UC13 - UC15)"])


@router.post("/list", response_model=BaseResponse[PlanListResponseData])
async def list_plans(
    req: BaseRequest[EmptyData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    plans = plan_service.list_plans(session, user_id)
    return BaseResponse(
        action="PLAN_GET_LIST",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=PlanListResponseData(plans=[PlanItem(**item) for item in plans]),
    )


@router.post("/create", response_model=BaseResponse[PlanItem])
async def create_plan(
    req: BaseRequest[PlanCreateRequestData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    plan_name = req.data.planName.strip()
    if not plan_name or req.data.targetMinutes <= 0:
        return BaseResponse(
            action="PLAN_CREATE",
            requestId=req.requestId,
            success=False,
            errorCode="PLAN_EMPTY_INFO",
            message="Thông tin không được để trống.",
            data=None,
        )

    created = plan_service.create_plan(
        session=session,
        user_id=user_id,
        plan_name=plan_name,
        target_minutes=req.data.targetMinutes,
    )
    return BaseResponse(
        action="PLAN_CREATE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Tạo kế hoạch học tập thành công.",
        data=PlanItem(**created),
    )


@router.post("/update", response_model=BaseResponse[None])
async def update_plan(
    req: BaseRequest[PlanUpdateRequestData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    plan_name = req.data.planName.strip()
    if req.data.planId <= 0 or not plan_name or req.data.targetMinutes <= 0:
        return BaseResponse(
            action="PLAN_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="PLAN_NOT_FOUND",
            message="Thông tin trống hoặc không tìm thấy kế hoạch.",
            data=None,
        )

    updated = plan_service.update_plan(
        session=session,
        user_id=user_id,
        plan_id=req.data.planId,
        plan_name=plan_name,
        target_minutes=req.data.targetMinutes,
    )
    if updated is None:
        return BaseResponse(
            action="PLAN_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="PLAN_NOT_FOUND",
            message="Thông tin trống hoặc không tìm thấy kế hoạch.",
            data=None,
        )

    return BaseResponse(
        action="PLAN_UPDATE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Cập nhật kế hoạch học tập thành công.",
        data=None,
    )


@router.post("/delete", response_model=BaseResponse[None])
async def delete_plan(
    req: BaseRequest[PlanDeleteRequestData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if req.data.planId <= 0:
        return BaseResponse(
            action="PLAN_DELETE",
            requestId=req.requestId,
            success=False,
            errorCode="PLAN_NOT_FOUND",
            message="Không tìm thấy kế hoạch.",
            data=None,
        )

    deleted = plan_service.delete_plan(
        session=session,
        user_id=user_id,
        plan_id=req.data.planId,
    )
    if not deleted:
        return BaseResponse(
            action="PLAN_DELETE",
            requestId=req.requestId,
            success=False,
            errorCode="PLAN_NOT_FOUND",
            message="Không tìm thấy kế hoạch.",
            data=None,
        )

    return BaseResponse(
        action="PLAN_DELETE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã xóa kế hoạch học tập.",
        data=None,
    )
