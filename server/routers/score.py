from fastapi import APIRouter, Depends

from dependencies import get_current_user_id
from schemas.base import BaseRequest, BaseResponse
from schemas.score import (
    ScoreEstimateRequestData,
    ScoreEstimateResponseData,
)
from services import score_service

router = APIRouter(prefix="/api/score", tags=["Score & GPA (UC18)"])


@router.post("/estimate", response_model=BaseResponse[ScoreEstimateResponseData])
async def estimate_gpa(
    req: BaseRequest[ScoreEstimateRequestData],
    user_id: int = Depends(get_current_user_id),
):
    ok, required_score, msg = score_service.estimate_required_score(
        current_scores=[item.model_dump() for item in req.data.currentScores],
        remaining_weight_percent=req.data.remainingWeightPercent,
        target_gpa=req.data.targetGPA,
        scale=req.data.scale,
    )
    if not ok or required_score is None:
        return BaseResponse(
            action="SCORE_ESTIMATE_GPA",
            requestId=req.requestId,
            success=False,
            errorCode="SCORE_TARGET_UNACHIEVABLE",
            message=msg,
            data=None,
        )

    return BaseResponse(
        action="SCORE_ESTIMATE_GPA",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=ScoreEstimateResponseData(
            requiredScoreForRemainingWeight=required_score,
        ),
    )
