from __future__ import annotations

from datetime import UTC, datetime, timedelta

from models import LoginSession, PomodoroSettings, User
from sqlmodel import Session, select


def utc_now() -> datetime:
    return datetime.now(UTC)


def register_user(
    db: Session, username: str, password: str, display_name: str | None = None
) -> User:
    username = username.strip()
    display_name = (display_name or username).strip()

    if not username:
        raise ValueError("Tên đăng nhập không được để trống.")
    if not password:
        raise ValueError("Mật khẩu không được để trống.")
    if not display_name:
        raise ValueError("Tên hiển thị không được để trống.")

    existing = db.exec(select(User).where(User.username == username)).first()
    if existing:
        raise ValueError("Tên đăng nhập đã tồn tại.")

    user = User(username=username, display_name=display_name, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(PomodoroSettings(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


def login_user(
    db: Session, username: str, password: str, lifetime_hours: int = 24
) -> str:
    if lifetime_hours <= 0:
        raise ValueError("Thời hạn đăng nhập phải lớn hơn 0.")
    user = db.exec(select(User).where(User.username == username.strip())).first()

    if user is None or user.password != password:
        raise ValueError("Tên đăng nhập hoặc mật khẩu không chính xác.")

    token = f"user-{user.id}-{utc_now().timestamp()}"
    login_session = LoginSession(
        user_id=user.id,
        token_hash=token,
        created_at=utc_now(),
        expires_at=utc_now() + timedelta(hours=lifetime_hours),
    )
    db.add(login_session)
    db.commit()
    return token


def logout_user(db: Session, token: str) -> bool:
    if not token:
        return False
    login_session = db.exec(
        select(LoginSession).where(
            LoginSession.token_hash == token,
            LoginSession.revoked_at.is_(None),
        )
    ).first()

    if login_session is None:
        return False
    login_session.revoked_at = utc_now()
    db.add(login_session)
    db.commit()
    return True


def get_profile(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Không tìm thấy tài khoản.")
    return user


def update_profile(
    db: Session,
    user_id: int,
    *,
    display_name: str | None = None,
    old_password: str | None = None,
    new_password: str | None = None,
) -> User:
    if display_name is not None and not display_name.strip():
        raise ValueError("Tên hiển thị không được để trống.")
    if (old_password is None) != (new_password is None):
        raise ValueError("Khi đổi mật khẩu, cần nhập cả mật khẩu cũ và mật khẩu mới.")
    if new_password is not None and not new_password:
        raise ValueError("Mật khẩu mới không được để trống.")

    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Không tìm thấy tài khoản.")

    if display_name is not None:
        user.display_name = display_name.strip()
    if old_password is not None and new_password is not None:
        if old_password != user.password:
            raise ValueError("Mật khẩu cũ không chính xác.")
        user.password = new_password

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
