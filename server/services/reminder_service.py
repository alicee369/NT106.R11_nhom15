from typing import Dict
from sqlmodel import Session

_configs: Dict[int, dict] = {}

DEFAULT_CONFIG = {
    "studyReminder": {"enabled": True, "notifyBeforeMinutes": 15},
    "breakReminder": {"enabled": True, "notifyBeforeMinutes": 5},
    "deadlineReminder": {"enabled": True, "notifyBeforeMinutes": 60},
}


def get_reminder_config(session: Session, user_id: int) -> dict:
    return _configs.get(user_id, DEFAULT_CONFIG)


def update_reminder_config(session: Session, user_id: int, config: dict) -> dict:
    _configs[user_id] = config
    return _configs[user_id]