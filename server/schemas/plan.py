from typing import List
from pydantic import BaseModel


class PlanItem(BaseModel):
    planId: int
    planName: str
    targetMinutes: int
    progressPercent: float
    studiedMinutes: int


class PlanListResponseData(BaseModel):
    plans: List[PlanItem]


class PlanCreateRequestData(BaseModel):
    planName: str
    targetMinutes: int


class PlanUpdateRequestData(BaseModel):
    planId: int
    planName: str
    targetMinutes: int


class PlanDeleteRequestData(BaseModel):
    planId: int

