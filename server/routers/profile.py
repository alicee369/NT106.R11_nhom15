from fastapi import APIRouter, Header, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlmodel import Session, select, delete
from database import get_session
from Models import User, LoginSession, StudyPlan, PomodoroSettings

router = APIRouter(prefix="/api/profile", tags=["Profile"])

class RequestPayload(BaseModel):
    action: str
    requestId: int
    data: Dict[str, Any]

def build_response(action: str, req_id: int, success: bool, error_code: Optional[str], message: str, data: Optional[Dict] = None):
    return {
        "action": action,
        "requestId": req_id,
        "success": success,
        "errorCode": error_code,
        "message": message,
        "data": data
    }

# Lấy user_id từ token
def get_current_user_id(authorization: Optional[str]) -> int:
    if authorization and authorization.startswith("Bearer "):
        try:
            # Lấy id ở phần đuôi của token mà ta đã tạo lúc login
            token = authorization.split(" ")[1]
            return int(token.split("...")[-1])
        except Exception:
            pass
    # Nếu client không gửi Auth header, trả về 0 để server báo lỗi "USER_NOT_FOUND"
    return 0

# UC25: Xem hồ sơ người dùng
@router.post("")
async def get_profile(payload: RequestPayload, authorization: Optional[str] = Header(None), session: Session = Depends(get_session)):
    user_id = get_current_user_id(authorization)
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        return build_response("PROFILE_GET", payload.requestId, False, "USER_NOT_FOUND", "Không tìm thấy người dùng", None)

    return build_response(
        action="PROFILE_GET",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Lấy thông tin hồ sơ thành công.",
        data={
            "userId": user.id,
            "username": user.username,
            "displayName": user.display_name,
            "joinDate": user.created_at.isoformat() if user.created_at else None
        }
    )

# UC26: Cập nhật thông tin cá nhân
@router.post("/update")
async def update_profile(payload: RequestPayload, authorization: Optional[str] = Header(None), session: Session = Depends(get_session)):
    user_id = get_current_user_id(authorization)
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        return build_response("PROFILE_UPDATE", payload.requestId, False, "USER_NOT_FOUND", "Không tìm thấy người dùng", None)



    display_name: Optional[str] = payload.data.get("displayName")
    old_password: Optional[str] = payload.data.get("oldPassword")
    new_password: Optional[str] = payload.data.get("newPassword")

    # Nếu người dùng muốn đổi mật khẩu
    if old_password and new_password:
        if user.password != old_password:
            return build_response(
                action="PROFILE_UPDATE",
                req_id=payload.requestId,
                success=False,
                error_code="PROFILE_WRONG_OLD_PASSWORD",
                message="Mật khẩu cũ không chính xác. Không thể đổi mật khẩu mới.",
                data=None
            )
        user.password = new_password

    # Nếu người dùng đổi tên hiển thị
    if display_name:
        user.display_name = display_name

    session.add(user)
    session.commit()
    session.refresh(user)

    return build_response(
        action="PROFILE_UPDATE",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Cập nhật hồ sơ thành công.",
        data={"displayName": user.display_name}
    )

# UC27: Xóa tài khoản
@router.post("/delete")
async def delete_profile(payload: RequestPayload, authorization: Optional[str] = Header(None), session: Session = Depends(get_session)):
    user_id = get_current_user_id(authorization)
    user = session.exec(select(User).where(User.id == user_id)).first()

    password_to_confirm = payload.data.get("passwordToConfirm")

    if not user:
        return build_response("PROFILE_DELETE", payload.requestId, False, "USER_NOT_FOUND", "Không tìm thấy người dùng", None)

    # Xác thực mật khẩu trước khi xóa
    if user.password != password_to_confirm:
        return build_response(
            action="PROFILE_DELETE",
            req_id=payload.requestId,
            success=False,
            error_code="PROFILE_WRONG_PASSWORD",
            message="Mật khẩu xác nhận không chính xác.",
            data=None
        )

    # --- DỌN DẸP DỮ LIỆU CON TRƯỚC KHI XÓA USER ---
    session.exec(delete(LoginSession).where(LoginSession.user_id == user.id))
    session.exec(delete(PomodoroSettings).where(PomodoroSettings.user_id == user.id))
    session.exec(delete(StudyPlan).where(StudyPlan.user_id == user.id))
    # ---------------------------------------------------------

    # Xóa User
    session.delete(user)
    session.commit()

    return build_response(
        action="PROFILE_DELETE",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Tài khoản và toàn bộ dữ liệu của bạn đã được xóa vĩnh viễn.",
        data=None
    )