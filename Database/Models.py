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
        CheckConstraint("focus_min > 0", name="ck_pomo_focus"),
        CheckConstraint("break_min > 0", name="ck_pomo_break"),
        CheckConstraint(
            "lbreak_min IS NULL OR lbreak_min > 0",
            name="ck_pomo_lbreak",
        ),
    )
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    focus_min: int = Field(default=25)
    break_min: int = Field(default=5)
    lbreak_min: int | None = Field(default=None)


class StudyPlan(SQLModel, table=True):
    __tablename__ = "study_plans"
    __table_args__ = (CheckConstraint("target_min > 0", name="ck_plans_target"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
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
