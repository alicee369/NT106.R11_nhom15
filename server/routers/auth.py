from fastapi import APIRouter, Header, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlmodel import Session, select

# Import get_session và Model từ project của bạn
from database import get_session
from Models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

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

# UC22: Tạo tài khoản
@router.post("/register")
async def register(payload: RequestPayload, session: Session = Depends(get_session)):
    username = payload.data.get("username")
    password = payload.data.get("password")
    display_name = payload.data.get("displayName")

    # Kiểm tra xem tên đăng nhập đã tồn tại trong database chưa
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        return build_response(
            action="AUTH_REGISTER",
            req_id=payload.requestId,
            success=False,
            error_code="AUTH_USERNAME_EXISTS",
            message="Tên đăng nhập này đã có người sử dụng. Vui lòng chọn tên khác.",
            data=None
        )

    # Thêm user mới vào DB
    new_user = User(username=username, password=password, display_name=display_name)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return build_response(
        action="AUTH_REGISTER",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đăng ký tài khoản thành công. Bạn có thể đăng nhập ngay.",
        data={"userId": new_user.id, "username": new_user.username}
    )

# UC23: Đăng nhập
@router.post("/login")
async def login(payload: RequestPayload, session: Session = Depends(get_session)):
    username = payload.data.get("username")
    password = payload.data.get("password")

    # Truy vấn lấy user theo username
    user = session.exec(select(User).where(User.username == username)).first()

    # Kiểm tra user có tồn tại không và password có khớp không
    if not user or user.password != password:
        return build_response(
            action="AUTH_LOGIN",
            req_id=payload.requestId,
            success=False,
            error_code="AUTH_INVALID_CREDENTIALS",
            message="Tên đăng nhập hoặc mật khẩu không chính xác.",
            data=None
        )

    # Trả về token mô phỏng, đính kèm luôn id để test auth header ở phần profile
    fake_token = f"eyJhbGciOiJIUzI1Ni...{user.id}"

    return build_response(
        action="AUTH_LOGIN",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đăng nhập thành công",
        data={
            "userId": user.id,
            "displayName": user.display_name,
            "token": fake_token
        }
    )

# UC24: Đăng xuất
@router.post("/logout")
async def logout(payload: RequestPayload, authorization: Optional[str] = Header(None)):
    return build_response(
        action="AUTH_LOGOUT",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đã đăng xuất thành công.",
        data=None
    )