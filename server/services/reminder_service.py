import copy
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlmodel import Session

from services import schedule_service

_configs: Dict[int, dict] = {}

DEFAULT_CONFIG = {
    "studyReminder": {"enabled": True, "notifyBeforeMinutes": 15},
    "breakReminder": {"enabled": True, "notifyBeforeMinutes": 5},
    "deadlineReminder": {"enabled": True, "notifyBeforeMinutes": 60},
}

# Ánh xạ eventType của Lịch biểu sang nhóm cấu hình UC12
EVENT_TO_REMINDER_MAP = {
    "STUDY": ("studyReminder", "STUDY", "giờ học"),
    "EXAM": ("deadlineReminder", "DEADLINE", "lịch thi"),
    "DEADLINE": ("deadlineReminder", "DEADLINE", "deadline"),
}


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_reminder_config(session: Session, user_id: int) -> dict:
    saved = _configs.get(user_id)
    return copy.deepcopy(saved) if saved is not None else copy.deepcopy(DEFAULT_CONFIG)


def update_reminder_config(session: Session, user_id: int, config: dict) -> dict:
    _configs[user_id] = copy.deepcopy(config)
    return copy.deepcopy(_configs[user_id])


def get_upcoming_reminders(
    session: Session,
    user_id: int,
    window_minutes: Optional[int] = 1440,
    only_due_now: bool = False,
) -> dict:
    now = datetime.now(timezone.utc)
    cfg = get_reminder_config(session, user_id)
    events = schedule_service.get_user_events(session, user_id)

    upcoming: List[dict] = []

    for ev in events:
        mapping = EVENT_TO_REMINDER_MAP.get(ev["event_type"])
        if mapping is None:
            continue

        cfg_key, reminder_type, label = mapping
        item_cfg = cfg.get(cfg_key, {})

        # Bỏ qua nếu người dùng đang tắt loại nhắc nhở này
        if not item_cfg.get("enabled", False):
            continue

        start_time: datetime = ev["start_time"]
        end_time: datetime = ev["end_time"]

        # Bỏ qua sự kiện đã bắt đầu quá 60 giây (giữ biên 60s cho trường hợp báo trước 0 phút)
        if start_time < now - timedelta(seconds=60):
            continue

        notify_before = max(0, int(item_cfg.get("notifyBeforeMinutes", 0)))
        notify_at = start_time - timedelta(minutes=notify_before)
        is_due = notify_at <= now

        if only_due_now and not is_due:
            continue

        if window_minutes is not None and not is_due:
            if notify_at > now + timedelta(minutes=window_minutes):
                continue

        seconds_left = int((start_time - now).total_seconds())
        minutes_left = max(0, (seconds_left + 59) // 60)

        if minutes_left == 0:
            msg = f"Đã đến {label} '{ev['title']}'!"
        else:
            msg = f"Sắp đến {label} '{ev['title']}' (còn {minutes_left} phút)."

        upcoming.append(
            {
                "eventId": ev["event_id"],
                "title": ev["title"],
                "eventType": ev["event_type"],
                "reminderType": reminder_type,
                "startTime": _to_iso(start_time),
                "endTime": _to_iso(end_time),
                "notifyBeforeMinutes": notify_before,
                "notifyAt": _to_iso(notify_at),
                "isDue": is_due,
                "message": msg,
            }
        )

    upcoming.sort(key=lambda item: item["notifyAt"])

    return {
        "serverTime": _to_iso(now),
        "reminders": upcoming,
    }