from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select
from sqlmodel import Session, col, select
from database import get_session
from Models import LoginSession

security = HTTPBearer(auto_error=False)


class AuthError(Exception):
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session),
) -> int:
    if credentials is None or not credentials.credentials:
        raise AuthError(
            error_code="UNAUTHORIZED",
            message="Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.",
        )

    token = credentials.credentials
    login_session = session.exec(
        select(LoginSession).where(
            LoginSession.token_hash == token,
            col(LoginSession.revoked_at).is_(None),
        )
    ).first()

    if not login_session:
        raise AuthError(
            error_code="TOKEN_INVALID",
            message="Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.",
        )

    if login_session.expires_at is not None:
        expires_at = login_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise AuthError(
                error_code="TOKEN_EXPIRED",
                message="Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.",
            )

    return int(login_session.user_id)