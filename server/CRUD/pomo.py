from __future__ import annotations

from datetime import UTC, datetime

from Models import PomodoroSettings, StudyPlan, pomo_session
from sqlmodel import Session, select


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_pomo_setting(db: Session, user_id: int) -> PomodoroSettings:
    return db.get(PomodoroSettings, user_id)


def update_pomo_setting(
    db: Session,
    user_id: int,
    *,
    focus_min: int | None = None,
    break_min: int | None = None,
    lbreak_min: int | None = None,
    clear_lbreak: bool = False,
    reminder_enabled: bool | None = None,
    reminder_advance_min: int | None = None,
) -> PomodoroSettings:
    if focus_min is not None and focus_min <= 0:
        raise ValueError("Thời gian học phải lớn hơn 0 phút.")
    if break_min is not None and break_min <= 0:
        raise ValueError("Thời gian nghỉ ngắn phải lớn hơn 0 phút.")
    if lbreak_min is not None and lbreak_min <= 0:
        raise ValueError("Thời gian nghỉ dài phải lớn hơn 0 phút.")
    if reminder_advance_min is not None and reminder_advance_min < 0:
        raise ValueError("Thời gian báo trước không được nhỏ hơn 0 phút.")

    settings = get_pomo_setting(db, user_id)

    if focus_min is not None:
        settings.focus_min = focus_min
    if break_min is not None:
        settings.break_min = break_min
    if clear_lbreak:
        settings.lbreak_min = None
    elif lbreak_min is not None:
        settings.lbreak_min = lbreak_min
    if reminder_enabled is not None:
        settings.reminder_enabled = reminder_enabled
    if reminder_advance_min is not None:
        settings.reminder_advance_min = reminder_advance_min

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def create_pomo_session(
    session: Session,
    user_id: int,
    duration_min: int,
    plan_id: int | None = None,
) -> pomo_session:
    if plan_id is not None:
        plan = session.exec(
            select(StudyPlan).where(
                StudyPlan.id == plan_id, StudyPlan.user_id == user_id
            )
        ).first()
        if not plan:
            raise ValueError(
                "Kế hoạch học tập không tồn tại hoặc không thuộc quyền sở hữu"
            )

    pomo = pomo_session(
        user_id=user_id,
        plan_id=plan_id,
        duration_min=duration_min,
    )
    session.add(pomo)
    session.commit()
    session.refresh(pomo)
    return pomo
