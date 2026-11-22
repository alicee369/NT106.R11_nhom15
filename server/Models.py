from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(username) > 0", name="ck_usr_name"),
        CheckConstraint("length(password) > 0", name="ck_usr_pwd"),
    )

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    display_name: str = Field(max_length=100)
    password: str = Field(max_length=255)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )


class LoginSession(SQLModel, table=True):
    __tablename__ = "login_session"
    __table_args__ = (CheckConstraint("expires_at > created_at", name="ck_sess_exp"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    token_hash: str = Field(max_length=255, unique=True, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))
    revoked_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )


class PomodoroSettings(SQLModel, table=True):
    __tablename__ = "pomodoro_settings"
    __table_args__ = (
        CheckConstraint("focus_min > 0", name="ck_pomo_focus"),
        CheckConstraint("break_min > 0", name="ck_pomo_break"),
        CheckConstraint(
            "lbreak_min IS NULL OR lbreak_min > 0",
            name="ck_pomo_lbreak",
        ),
    )
    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    focus_min: int = Field(default=25)
    break_min: int = Field(default=5)
    lbreak_min: int | None = Field(default=None)


class StudyPlan(SQLModel, table=True):
    __tablename__ = "study_plans"
    __table_args__ = (CheckConstraint("target_min > 0", name="ck_plans_target"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    name: str = Field(max_length=150)
    target_min: int
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utc_now},
    )


class pomo_session(SQLModel, table=True):
    __tablename__ = "pomo_session"
    __table_args__ = (CheckConstraint("duration_min>=0", name="ck_duration_min"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    plan_id: int | None = Field(
        default=None, foreign_key="study_plans.id", ondelete="SET NULL"
    )
    duration_min: int
    completed_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )


class schedule_events(SQLModel, table=True):
    __tablename__ = "schedule_events"
    __table_args__ = (CheckConstraint("end_time>=start_time", name="ck_timing"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    title: str = Field(max_length=255)
    event_type: str | None = Field(
        default=None, max_length=50
    )  ##Phân loại sự kiện như kiểu: deadline, hay đi chơi, hay cái gì đó bla bla
    start_time: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    end_time: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )


class notes(SQLModel, table=True):
    __tablename__ = "notes"
    __table_args__ = (CheckConstraint("length(trim(content))>0", name="ck_content"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    title: str = Field(max_length=255)
    content: str
    is_todo: bool = Field(default=False)
    is_completed: bool = Field(default=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utc_now},
    )


class reminder(SQLModel, table=True):
    __tablename__ = "reminder_configs"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")

    study_enabled: bool = Field(default=True)
    study_before_min: int = Field(default=15, ge=0)

    break_enabled: bool = Field(default=True)
    break_before_min: int = Field(default=5, ge=0)

    deadline_enabled: bool = Field(default=True)
    deadline_before_min: int = Field(default=60, ge=0)
