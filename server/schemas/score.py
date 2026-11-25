from typing import List
from pydantic import BaseModel


class CurrentScoreItem(BaseModel):
    score: float
    weightPercent: float


class ScoreEstimateRequestData(BaseModel):
    currentScores: List[CurrentScoreItem]
    remainingWeightPercent: float
    targetGPA: float
    scale: float


class ScoreEstimateResponseData(BaseModel):
    requiredScoreForRemainingWeight: float
    