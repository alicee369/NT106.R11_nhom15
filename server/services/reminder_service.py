from datetime import datetime, timedelta, timezone
from typing import List, Optional

from CRUD import reminder as reminder_crud
from Models import reminder
from services import schedule_service
from sqlmodel import Session

# Ánh xạ eventType của Lịch biểu sang nhóm cấu hình UC12
EVENT_TO_REMINDER_MAP = {
    "STUDY": ("studyReminder", "STUDY", "giờ học"),
    "EXAM": ("deadlineReminder", "DEADLINE", "lịch thi"),
    "DEADLINE": ("deadlineReminder", "DEADLINE", "deadline"),
}


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_reminder_config(session: Session, user_id: int) -> reminder:
    """Đảm bảo user cũ (chưa có dòng trong reminder_configs) vẫn có bản ghi mặc định."""
    cfg = reminder_crud.get_reminder_config(session, user_id)
    if cfg is None:
        cfg = reminder(user_id=user_id)
        session.add(cfg)
        session.commit()
        session.refresh(cfg)
    return cfg


def _model_to_dict(cfg: reminder) -> dict:
    return {
        "studyReminder": {
            "enabled": cfg.study_enabled,
            "notifyBeforeMinutes": cfg.study_before_min,
        },
        "breakReminder": {
            "enabled": cfg.break_enabled,
            "notifyBeforeMinutes": cfg.break_before_min,
        },
        "deadlineReminder": {
            "enabled": cfg.deadline_enabled,
            "notifyBeforeMinutes": cfg.deadline_before_min,
        },
    }


def get_reminder_config(session: Session, user_id: int) -> dict:
    cfg = _ensure_reminder_config(session, user_id)
    return _model_to_dict(cfg)


def update_reminder_config(session: Session, user_id: int, config: dict) -> dict:
    _ensure_reminder_config(session, user_id)
    study = config.get("studyReminder", {})
    brk = config.get("breakReminder", {})
    deadline = config.get("deadlineReminder", {})

    updated = reminder_crud.update_reminder_config(
        db=session,
        user_id=user_id,
        study_enabled=study.get("enabled"),
        study_before_min=study.get("notifyBeforeMinutes"),
        break_enabled=brk.get("enabled"),
        break_before_min=brk.get("notifyBeforeMinutes"),
        deadline_enabled=deadline.get("enabled"),
        deadline_before_min=deadline.get("notifyBeforeMinutes"),
    )
    return _model_to_dict(updated)


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