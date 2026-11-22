from datetime import datetime, timezone
from typing import Dict, List, Optional

from CRUD import pomo as pomo_crud
from Models import PomodoroSettings
from sqlmodel import Session

# Trạng thái phiên đang chạy (RUNNING/PAUSED) và cờ Mini-player tạm giữ trên RAM
# vì bảng pomo_session chỉ lưu lịch sử phiên đã kết thúc và pomodoro_settings chưa có cột mini-player.
_sessions: Dict[int, dict] = {}
_next_session_id = 1
_miniplayer: Dict[int, bool] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_pomo_setting(session: Session, user_id: int) -> PomodoroSettings:
    """Đảm bảo user cũ (chưa có dòng trong pomodoro_settings) vẫn có bản ghi mặc định."""
    settings = pomo_crud.get_pomo_setting(session, user_id)
    if settings is None:
        settings = PomodoroSettings(user_id=user_id, focus_min=25, break_min=5)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


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

    # Lưu lịch sử phiên học xuống bảng pomo_session trên Supabase
    duration_min = max(0, record["accumulated_seconds"] // 60)
    try:
        pomo_crud.create_pomo_session(
            session=session,
            user_id=user_id,
            duration_min=duration_min,
            plan_id=record["plan_id"],
        )
    except ValueError:
        # Nếu plan_id chưa tồn tại trong study_plans thì vẫn lưu lịch sử phiên học với plan_id=None
        pomo_crud.create_pomo_session(
            session=session,
            user_id=user_id,
            duration_min=duration_min,
            plan_id=None,
        )

    newly_unlocked_badges: List[dict] = []
    return {
        "plannedDurationSeconds": record["focus_minutes"] * 60,
        "actualDurationSeconds": record["accumulated_seconds"],
        "endTime": _to_iso(now),
        "newlyUnlockedBadges": newly_unlocked_badges,
    }


def get_settings(session: Session, user_id: int) -> dict:
    settings = _ensure_pomo_setting(session, user_id)
    return {
        "focusMinutes": settings.focus_min,
        "breakMinutes": settings.break_min,
    }


def update_settings(
    session: Session, user_id: int, focus_minutes: int, break_minutes: int
) -> dict:
    _ensure_pomo_setting(session, user_id)
    updated = pomo_crud.update_pomo_setting(
        session,
        user_id,
        focus_min=focus_minutes,
        break_min=break_minutes,
    )
    return {
        "focusMinutes": updated.focus_min,
        "breakMinutes": updated.break_min,
    }


def get_miniplayer_preference(session: Session, user_id: int) -> bool:
    return _miniplayer.get(user_id, False)


def sync_miniplayer_preference(
    session: Session, user_id: int, is_mini_player: bool
) -> None:
    _miniplayer[user_id] = is_mini_player
