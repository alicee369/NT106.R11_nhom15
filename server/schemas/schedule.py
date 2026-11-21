from datetime import datetime
from typing import List
from pydantic import BaseModel
from schemas.base import EventType, ViewModeType


class ScheduleListData(BaseModel):
    viewMode: ViewModeType
    startDate: str
    endDate: str
    timezone: str


class ScheduleEventItem(BaseModel):
    eventId: int
    title: str
    eventType: EventType
    startTime: str
    endTime: str


class ScheduleListResponseData(BaseModel):
    events: List[ScheduleEventItem]


class ScheduleAddData(BaseModel):
    title: str
    eventType: EventType
    startTime: datetime
    endTime: datetime


class ScheduleUpdateData(BaseModel):
    eventId: int
    title: str
    eventType: EventType
    startTime: datetime
    endTime: datetime


class ScheduleDeleteData(BaseModel):
    eventId: int