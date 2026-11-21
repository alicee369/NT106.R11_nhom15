from pydantic import BaseModel


class ReminderItemConfig(BaseModel):
    enabled: bool
    notifyBeforeMinutes: int


class ReminderConfigData(BaseModel):
    studyReminder: ReminderItemConfig
    breakReminder: ReminderItemConfig
    deadlineReminder: ReminderItemConfig