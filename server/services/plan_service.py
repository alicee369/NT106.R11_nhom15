from datetime import datetime, timezone
from typing import Dict, List, Optional

from Models import StudyPlan, pomo_session
from sqlalchemy import func
from sqlmodel import Session, select


def _calc_progress(studied_minutes: int, target_minutes: int) -> float:
    if target_minutes <= 0:
        return 0.0
    percent = (studied_minutes / target_minutes) * 100.0
    return round(min(100.0, max(0.0, percent)), 2)


def _to_plan_item_dict(plan: StudyPlan, studied_minutes: int) -> dict:
    return {
        "planId": int(plan.id),
        "planName": plan.name,
        "targetMinutes": plan.target_min,
        "progressPercent": _calc_progress(studied_minutes, plan.target_min),
        "studiedMinutes": studied_minutes,
    }


def list_plans(session: Session, user_id: int) -> List[dict]:
    plans = list(
        session.exec(
            select(StudyPlan)
            .where(StudyPlan.user_id == user_id)
            .order_by(StudyPlan.id.desc())
        ).all()
    )
    if not plans:
        return []

    # Tổng hợp số phút đã học theo từng plan_id trong 1 câu truy vấn duy nhất
    rows = session.exec(
        select(
            pomo_session.plan_id,
            func.coalesce(func.sum(pomo_session.duration_min), 0),
        )
        .where(
            pomo_session.user_id == user_id,
            pomo_session.plan_id.is_not(None),
        )
        .group_by(pomo_session.plan_id)
    ).all()
    studied_map: Dict[int, int] = {int(pid): int(total) for pid, total in rows if pid is not None}

    return [
        _to_plan_item_dict(plan, studied_map.get(int(plan.id), 0))
        for plan in plans
    ]


def create_plan(
    session: Session,
    user_id: int,
    plan_name: str,
    target_minutes: int,
) -> dict:
    plan = StudyPlan(
        user_id=user_id,
        name=plan_name.strip(),
        target_min=target_minutes,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return _to_plan_item_dict(plan, studied_minutes=0)


def update_plan(
    session: Session,
    user_id: int,
    plan_id: int,
    plan_name: str,
    target_minutes: int,
) -> Optional[dict]:
    plan = session.exec(
        select(StudyPlan).where(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == user_id,
        )
    ).first()
    if plan is None:
        return None

    plan.name = plan_name.strip()
    plan.target_min = target_minutes
    plan.updated_at = datetime.now(timezone.utc)
    session.add(plan)
    session.commit()
    session.refresh(plan)

    studied = session.exec(
        select(func.coalesce(func.sum(pomo_session.duration_min), 0)).where(
            pomo_session.user_id == user_id,
            pomo_session.plan_id == plan_id,
        )
    ).one()
    return _to_plan_item_dict(plan, studied_minutes=int(studied or 0))


def delete_plan(session: Session, user_id: int, plan_id: int) -> bool:
    plan = session.exec(
        select(StudyPlan).where(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == user_id,
        )
    ).first()
    if plan is None:
        return False

    # Giữ nguyên lịch sử phút học trong pomo_session bằng cách tách liên kết plan_id trước khi xóa
    linked_sessions = session.exec(
        select(pomo_session).where(
            pomo_session.user_id == user_id,
            pomo_session.plan_id == plan_id,
        )
    ).all()
    for ps in linked_sessions:
        ps.plan_id = None
        session.add(ps)

    session.delete(plan)
    session.commit()
    return True
