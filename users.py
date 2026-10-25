from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from models import (
    LoginSession,
    PomodoroSettings,
    Session,
    User,
    select,
)


def utc_now() -> datetime:
    return datetime.now(timezone.UTC)


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Mật khẩu không được để trống.")

    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return f"scrypt${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, expected_hex = stored_hash.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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

    user = User(
        username=username,
        display_name=display_name,
        password_hash=hash_password(password),
    )
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

    if user is None or not verify_password(password, user.password_hash):
        raise ValueError("Tên đăng nhập hoặc mật khẩu không chính xác.")

    raw_token = secrets.token_urlsafe(32)
    login_session = LoginSession(
        user_id=user.id,
        token_hash=_token_hash(raw_token),
        created_at=utc_now(),
        expires_at=utc_now() + timedelta(hours=lifetime_hours),
    )
    db.add(login_session)
    db.commit()
    return raw_token


def get_user_from_token(db: Session, token: str) -> User | None:
    if not token:
        return None

    now = utc_now()
    login_session = db.exec(
        select(LoginSession).where(
            LoginSession.token_hash == _token_hash(token),
            LoginSession.revoked_at.is_(None),
            LoginSession.expires_at > now,
        )
    ).first()

    if login_session is None:
        return None
    return db.get(User, login_session.user_id)


def logout_user(db: Session, token: str) -> bool:
    if not token:
        return False
    login_session = db.exec(
        select(LoginSession).where(
            LoginSession.token_hash == _token_hash(token),
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
        if not verify_password(old_password, user.password_hash):
            raise ValueError("Mật khẩu cũ không chính xác.")
        user.password_hash = hash_password(new_password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
