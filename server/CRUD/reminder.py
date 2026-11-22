from Models import reminder
from sqlmodel import Session


def get_reminder_config(db: Session, user_id: int) -> reminder | None:
    return db.get(reminder, user_id)


def update_reminder_config(
    db: Session,
    user_id: int,
    study_enabled: bool | None = None,
    study_before_min: int | None = None,
    break_enabled: bool | None = None,
    break_before_min: int | None = None,
    deadline_enabled: bool | None = None,
    deadline_before_min: int | None = None,
) -> reminder:
    config = get_reminder_config(db, user_id)
    if not config:
        raise ValueError("Không tìm thấy cấu hình nhắc nhở của người dùng.")

    # Kiểm tra thời gian báo trước không được âm
    for minutes in (study_before_min, break_before_min, deadline_before_min):
        if minutes is not None and minutes < 0:
            raise ValueError("Thời gian báo trước phải lớn hơn hoặc bằng 0 phút.")

    if study_enabled is not None:
        config.study_enabled = study_enabled
    if study_before_min is not None:
        config.study_before_min = study_before_min

    if break_enabled is not None:
        config.break_enabled = break_enabled
    if break_before_min is not None:
        config.break_before_min = break_before_min

    if deadline_enabled is not None:
        config.deadline_enabled = deadline_enabled
    if deadline_before_min is not None:
        config.deadline_before_min = deadline_before_min

    db.add(config)
    db.commit()
    db.refresh(config)
    return config
