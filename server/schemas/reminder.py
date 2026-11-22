from pydantic import BaseModel


class ReminderItemConfig(BaseModel):
    enabled: bool
    notifyBeforeMinutes: int


class reminderData(BaseModel):
    studyReminder: ReminderItemConfig
    breakReminder: ReminderItemConfig
    deadlineReminder: ReminderItemConfig
