from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from CRUD.user import register_user
from database import get_session
from fastapi import APIRouter, Depends, Header
from Models import LoginSession, User
from pydantic import BaseModel
from sqlmodel import Session, delete, select

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RequestPayload(BaseModel):
    action: str
    requestId: int
    data: Dict[str, Any]


def build_response(
    action: str,
    req_id: int,
    success: bool,
    error_code: Optional[str],
    message: str,
    data: Optional[Dict] = None,
):
    return {
        "action": action,
        "requestId": req_id,
        "success": success,
        "errorCode": error_code,
        "message": message,
        "data": data,
    }


# UC22: Tạo tài khoản (gọi CRUD/user.py để tự tạo PomodoroSettings & reminder)
@router.post("/register")
async def register(payload: RequestPayload, session: Session = Depends(get_session)):
    username = str(payload.data.get("username") or "").strip()
    password = str(payload.data.get("password") or "")
    raw_display_name = payload.data.get("displayName")
    display_name = (
        str(raw_display_name).strip() if raw_display_name else "Người Dùng Mới"
    )

    try:
        new_user = register_user(
            session,
            username=username,
            password=password,
            display_name=display_name,
        )
    except ValueError as e:
        err_msg = str(e)
        if "đã tồn tại" in err_msg.lower():
            return build_response(
                action="AUTH_REGISTER",
                req_id=payload.requestId,
                success=False,
                error_code="AUTH_USERNAME_EXISTS",
                message="Tên đăng nhập này đã có người sử dụng. Vui lòng chọn tên khác.",
                data=None,
            )
        return build_response(
            action="AUTH_REGISTER",
            req_id=payload.requestId,
            success=False,
            error_code="AUTH_INVALID_INPUT",
            message=err_msg,
            data=None,
        )

    return build_response(
        action="AUTH_REGISTER",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đăng ký tài khoản thành công. Bạn có thể đăng nhập ngay.",
        data={"userId": new_user.id, "username": new_user.username},
    )


# UC23: Đăng nhập
@router.post("/login")
async def login(payload: RequestPayload, session: Session = Depends(get_session)):
    username = str(payload.data.get("username") or "").strip()
    password = str(payload.data.get("password") or "")

    user = session.exec(select(User).where(User.username == username)).first()

    if not user:
        return build_response(
            action="AUTH_LOGIN",
            req_id=payload.requestId,
            success=False,
            error_code="AUTH_USER_NOT_FOUND",
            message="Tài khoản này chưa tồn tại",
            data=None,
        )

    if user.password != password:
        return build_response(
            action="AUTH_LOGIN",
            req_id=payload.requestId,
            success=False,
            error_code="AUTH_INVALID_CREDENTIALS",
            message="Mật khẩu không chính xác.",
            data=None,
        )

    fake_token = f"eyJhbGciOiJIUzI1Ni...{user.id}"
    expiry_time = datetime.now(timezone.utc) + timedelta(days=7)

    session.exec(delete(LoginSession).where(LoginSession.user_id == user.id))

    new_login_session = LoginSession(
        user_id=int(user.id),
        token_hash=fake_token,
        expires_at=expiry_time,
    )
    session.add(new_login_session)
    session.commit()

    return build_response(
        action="AUTH_LOGIN",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đăng nhập thành công",
        data={
            "userId": user.id,
            "displayName": user.display_name,
            "token": fake_token,
        },
    )


# UC24: Đăng xuất
@router.post("/logout")
async def logout(
    payload: RequestPayload,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
):
    if authorization:
        token = (
            authorization.replace("Bearer ", "")
            if "Bearer " in authorization
            else authorization
        )
        session.exec(delete(LoginSession).where(LoginSession.token_hash == token))
        session.commit()

    return build_response(
        action="AUTH_LOGOUT",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đã đăng xuất thành công.",
        data=None,
    )