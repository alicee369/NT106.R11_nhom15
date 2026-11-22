from datetime import datetime, timezone
from typing import List, Optional

from CRUD import schedule as schedule_crud
from Models import schedule_events
from sqlmodel import Session


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return _to_utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def _model_to_internal_dict(ev: schedule_events) -> dict:
    return {
        "event_id": ev.id,
        "user_id": ev.user_id,
        "title": ev.title,
        "event_type": ev.event_type or "STUDY",
        "start_time": _to_utc(ev.start_time),
        "end_time": _to_utc(ev.end_time),
    }


def has_conflict(
    session: Session,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_event_id: Optional[int] = None,
) -> bool:
    start_utc = _to_utc(start_time)
    end_utc = _to_utc(end_time)

    candidates = schedule_crud.get_schedule_events(
        session,
        user_id,
        start_time=start_utc,
        end_time=end_utc,
    )
    for ev in candidates:
        if exclude_event_id is not None and ev.id == exclude_event_id:
            continue
        ev_start = _to_utc(ev.start_time)
        ev_end = _to_utc(ev.end_time)
        # Trùng lịch khi 2 khoảng thời gian thực sự giao nhau (nối tiếp nhau không tính trùng)
        if ev_start < end_utc and ev_end > start_utc:
            return True
    return False


def list_events(
    session: Session,
    user_id: int,
    start_date: str,
    end_date: str,
) -> List[dict]:
    start_bound = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
    end_bound = datetime.fromisoformat(f"{end_date}T23:59:59.999999+00:00")

    events = schedule_crud.get_schedule_events(
        session,
        user_id,
        start_time=start_bound,
        end_time=end_bound,
    )
    return [
        {
            "eventId": ev.id,
            "title": ev.title,
            "eventType": ev.event_type or "STUDY",
            "startTime": _to_iso(ev.start_time),
            "endTime": _to_iso(ev.end_time),
        }
        for ev in events
    ]


def create_event(
    session: Session,
    user_id: int,
    title: str,
    event_type: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    ev = schedule_crud.create_schedule_event(
        db=session,
        user_id=user_id,
        title=title,
        start_time=_to_utc(start_time),
        end_time=_to_utc(end_time),
        event_type=event_type,
    )
    return _model_to_internal_dict(ev)


def update_event(
    session: Session,
    user_id: int,
    event_id: int,
    title: str,
    event_type: str,
    start_time: datetime,
    end_time: datetime,
) -> Optional[dict]:
    try:
        ev = schedule_crud.update_schedule_event(
            db=session,
            user_id=user_id,
            event_id=event_id,
            title=title,
            event_type=event_type,
            start_time=_to_utc(start_time),
            end_time=_to_utc(end_time),
        )
    except ValueError:
        return None
    return _model_to_internal_dict(ev)


def delete_event(session: Session, user_id: int, event_id: int) -> bool:
    try:
        return schedule_crud.delete_schedule_event(
            db=session,
            user_id=user_id,
            event_id=event_id,
        )
    except ValueError:
        return False


def get_user_events(session: Session, user_id: int) -> List[dict]:
    """Trả về toàn bộ sự kiện từ Supabase của user (dùng chung cho Schedule & Reminder)."""
    events = schedule_crud.get_schedule_events(session, user_id)
    return [_model_to_internal_dict(ev) for ev in events]
