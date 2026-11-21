from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlmodel import Session

# Kho tạm trên RAM theo user_id (Ngày 21/11 thay ruột các hàm bằng CRUD của Mẫn)
_sessions: Dict[int, dict] = {}
_next_session_id = 1
_settings: Dict[int, dict] = {}
_miniplayer: Dict[int, bool] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_active_session(session: Session, user_id: int) -> Optional[dict]:
    for item in _sessions.values():
        if item["user_id"] == user_id and item["status"] in ("RUNNING", "PAUSED"):
            return item
    return None


def create_session(
    session: Session,
    user_id: int,
    plan_id: Optional[int],
    focus_minutes: int,
    break_minutes: int,
) -> dict:
    global _next_session_id
    now = _utc_now()
    record = {
        "session_id": _next_session_id,
        "user_id": user_id,
        "plan_id": plan_id,
        "focus_minutes": focus_minutes,
        "break_minutes": break_minutes,
        "status": "RUNNING",
        "start_time": now,
        "last_resumed_at": now,
        "accumulated_seconds": 0,
        "end_time": None,
    }
    _sessions[_next_session_id] = record
    _next_session_id += 1
    return {
        "sessionId": record["session_id"],
        "startTime": _to_iso(now),
    }


def pause_session(session: Session, user_id: int, session_id: int) -> Optional[dict]:
    record = _sessions.get(session_id)
    if not record or record["user_id"] != user_id or record["status"] != "RUNNING":
        return None

    now = _utc_now()
    elapsed = int((now - record["last_resumed_at"]).total_seconds())
    record["accumulated_seconds"] += max(0, elapsed)
    record["status"] = "PAUSED"
    record["last_resumed_at"] = None
    return record


def resume_session(session: Session, user_id: int, session_id: int) -> Optional[dict]:
    record = _sessions.get(session_id)
    if not record or record["user_id"] != user_id or record["status"] != "PAUSED":
        return None

    record["status"] = "RUNNING"
    record["last_resumed_at"] = _utc_now()
    return {
        "status": record["status"],
        "accumulatedSeconds": record["accumulated_seconds"],
    }


def stop_session(session: Session, user_id: int, session_id: int) -> Optional[dict]:
    record = _sessions.get(session_id)
    if not record or record["user_id"] != user_id or record["status"] == "STOPPED":
        return None

    now = _utc_now()
    if record["status"] == "RUNNING" and record["last_resumed_at"] is not None:
        elapsed = int((now - record["last_resumed_at"]).total_seconds())
        record["accumulated_seconds"] += max(0, elapsed)

    record["status"] = "STOPPED"
    record["last_resumed_at"] = None
    record["end_time"] = now

    newly_unlocked_badges: List[dict] = []
    return {
        "plannedDurationSeconds": record["focus_minutes"] * 60,
        "actualDurationSeconds": record["accumulated_seconds"],
        "endTime": _to_iso(now),
        "newlyUnlockedBadges": newly_unlocked_badges,
    }


def get_settings(session: Session, user_id: int) -> dict:
    return _settings.get(user_id, {"focusMinutes": 25, "breakMinutes": 5})


def update_settings(
    session: Session, user_id: int, focus_minutes: int, break_minutes: int
) -> dict:
    _settings[user_id] = {
        "focusMinutes": focus_minutes,
        "breakMinutes": break_minutes,
    }
    return _settings[user_id]


def get_miniplayer_preference(session: Session, user_id: int) -> bool:
    return _miniplayer.get(user_id, False)


def sync_miniplayer_preference(
    session: Session, user_id: int, is_mini_player: bool
) -> None:
    _miniplayer[user_id] = is_mini_player