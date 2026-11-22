from __future__ import annotations

from datetime import datetime

from Models import schedule_events
from sqlmodel import Session, select


def get_schedule_events(
    db: Session,
    user_id: int,
    *,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> list[schedule_events]:
    stmt = select(schedule_events).where(schedule_events.user_id == user_id)

    if start_time is not None:
        stmt = stmt.where(schedule_events.end_time >= start_time)
    if end_time is not None:
        stmt = stmt.where(schedule_events.start_time <= end_time)

    stmt = stmt.order_by(schedule_events.start_time.asc())
    return list(db.exec(stmt).all())


# UC5: Thêm sự kiện lịch
def create_schedule_event(
    db: Session,
    user_id: int,
    title: str,
    start_time: datetime,
    end_time: datetime,
    event_type: str | None = None,
) -> schedule_events:
    title = title.strip()
    if not title:
        raise ValueError("Tiêu đề sự kiện không được để trống.")
    if end_time < start_time:
        raise ValueError("Thời gian kết thúc không được nhỏ hơn thời gian bắt đầu.")

    clean_type = event_type.strip() if event_type else None

    event = schedule_events(
        user_id=user_id,
        title=title,
        event_type=clean_type or None,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# UC6: Sửa sự kiện lịch
def update_schedule_event(
    db: Session,
    user_id: int,
    event_id: int,
    *,
    title: str | None = None,
    event_type: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> schedule_events:
    event = db.exec(
        select(schedule_events).where(
            schedule_events.id == event_id,
            schedule_events.user_id == user_id,
        )
    ).first()
    if event is None:
        raise ValueError("Không tìm thấy sự kiện.")

    new_start = start_time if start_time is not None else event.start_time
    new_end = end_time if end_time is not None else event.end_time
    if new_end < new_start:
        raise ValueError("Thời gian kết thúc không được nhỏ hơn thời gian bắt đầu.")

    if title is not None:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Tiêu đề sự kiện không được để trống.")
        event.title = clean_title

    if event_type is not None:
        event.event_type = event_type.strip() or None

    event.start_time = new_start
    event.end_time = new_end

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# UC7: Xóa sự kiện lịch
def delete_schedule_event(db: Session, user_id: int, event_id: int) -> bool:
    event = db.exec(
        select(schedule_events).where(
            schedule_events.id == event_id,
            schedule_events.user_id == user_id,
        )
    ).first()
    if event is None:
        raise ValueError("Không tìm thấy sự kiện.")

    db.delete(event)
    db.commit()
    return True
