from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("LEN(username) > 0", name="ck_users_username_not_empty"),
        CheckConstraint(
            "LEN(password_hash) > 0", name="ck_users_password_hash_not_empty"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    display_name: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )


class LoginSession(SQLModel, table=True):
    __tablename__ = "login_sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_login_sessions_expiry"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
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
        CheckConstraint("focus_minutes > 0", name="ck_pomodoro_focus_positive"),
        CheckConstraint("break_minutes > 0", name="ck_pomodoro_break_positive"),
        CheckConstraint(
            "long_break_minutes IS NULL OR long_break_minutes > 0",
            name="ck_pomodoro_long_break_positive",
        ),
    )
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    focus_minutes: int = Field(default=25)
    break_minutes: int = Field(default=5)
    long_break_minutes: int | None = Field(default=None)


class StudyPlan(SQLModel, table=True):
    __tablename__ = "study_plans"
    __table_args__ = (
        CheckConstraint("target_minutes > 0", name="ck_study_plans_target_positive"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=150)
    target_minutes: int
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utc_now},
    )
