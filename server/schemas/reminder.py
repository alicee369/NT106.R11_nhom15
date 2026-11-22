from typing import List, Optional
from pydantic import BaseModel
from schemas.base import EventType


class ReminderItemConfig(BaseModel):
    enabled: bool
    notifyBeforeMinutes: int


class ReminderConfigData(BaseModel):
    studyReminder: ReminderItemConfig
    breakReminder: ReminderItemConfig
    deadlineReminder: ReminderItemConfig


class ReminderUpcomingRequestData(BaseModel):
    # Khoảng thời gian quét trước (mặc định 1440 phút = 24 giờ; truyền None để lấy tất cả)
    windowMinutes: Optional[int] = 1440
    # True: chỉ trả về các nhắc nhở đã đến giờ bật pop-up (notifyAt <= hiện tại)
    onlyDueNow: bool = False


class UpcomingReminderItem(BaseModel):
    eventId: int
    title: str
    eventType: EventType
    reminderType: str  # "STUDY" hoặc "DEADLINE"
    startTime: str
    endTime: str
    notifyBeforeMinutes: int
    notifyAt: str
    isDue: bool
    message: str


class ReminderUpcomingResponseData(BaseModel):
    serverTime: str
    reminders: List[UpcomingReminderItem]