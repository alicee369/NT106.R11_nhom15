from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlmodel import Session

_events: Dict[int, dict] = {}
_next_event_id = 1


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return _to_utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def has_conflict(
    session: Session,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_event_id: Optional[int] = None,
) -> bool:
    start_utc = _to_utc(start_time)
    end_utc = _to_utc(end_time)

    for ev in _events.values():
        if ev["user_id"] != user_id:
            continue
        if exclude_event_id is not None and ev["event_id"] == exclude_event_id:
            continue
        # Trùng lịch khi 2 khoảng thời gian giao nhau
        if ev["start_time"] < end_utc and ev["end_time"] > start_utc:
            return True
    return False


def list_events(
    session: Session,
    user_id: int,
    start_date: str,
    end_date: str,
) -> List[dict]:
    start_bound = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
    end_bound = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")

    results = []
    for ev in _events.values():
        if ev["user_id"] != user_id:
            continue
        if ev["start_time"] <= end_bound and ev["end_time"] >= start_bound:
            results.append(
                {
                    "eventId": ev["event_id"],
                    "title": ev["title"],
                    "eventType": ev["event_type"],
                    "startTime": _to_iso(ev["start_time"]),
                    "endTime": _to_iso(ev["end_time"]),
                }
            )
    results.sort(key=lambda item: item["startTime"])
    return results


def create_event(
    session: Session,
    user_id: int,
    title: str,
    event_type: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    global _next_event_id
    record = {
        "event_id": _next_event_id,
        "user_id": user_id,
        "title": title.strip(),
        "event_type": event_type,
        "start_time": _to_utc(start_time),
        "end_time": _to_utc(end_time),
    }
    _events[_next_event_id] = record
    _next_event_id += 1
    return record


def update_event(
    session: Session,
    user_id: int,
    event_id: int,
    title: str,
    event_type: str,
    start_time: datetime,
    end_time: datetime,
) -> Optional[dict]:
    record = _events.get(event_id)
    if not record or record["user_id"] != user_id:
        return None

    record["title"] = title.strip()
    record["event_type"] = event_type
    record["start_time"] = _to_utc(start_time)
    record["end_time"] = _to_utc(end_time)
    return record


def delete_event(session: Session, user_id: int, event_id: int) -> bool:
    record = _events.get(event_id)
    if not record or record["user_id"] != user_id:
        return False
    del _events[event_id]
    return True


def get_user_events(session: Session, user_id: int) -> List[dict]:
    """Trả về toàn bộ sự kiện của user (tầng service dùng chung cho Schedule & Reminder)."""
    return [ev for ev in _events.values() if ev["user_id"] == user_id]