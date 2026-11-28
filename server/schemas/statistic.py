from typing import List, Literal, Optional
from pydantic import BaseModel

FilterType = Literal["DAY", "WEEK", "MONTH"]


class StatisticViewRequestData(BaseModel):
    filterType: FilterType
    timezone: Optional[str] = "Asia/Ho_Chi_Minh"
    subjectTag: Optional[str] = None


class StatisticChartItem(BaseModel):
    label: str
    subjectTag: str
    studyMinutes: int


class StatisticViewResponseData(BaseModel):
    totalStudyMinutes: int
    chartData: List[StatisticChartItem]
