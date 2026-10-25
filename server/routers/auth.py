from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
#Nhóm API xác thực (UC22-UC24)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Schema: Kiểm tra & Ép kiểu JSON đầu vào
class RequestPayload(BaseModel):
    action: str
    requestId: int
    data: Dict[str, Any]

# Format: Chuẩn hóa JSON đầu ra
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
async def register(payload: RequestPayload):
    username = payload.data.get("username")
    # Trả về format JSON đã chốt cho đăng ký thành công
    return build_response(
        action="AUTH_REGISTER",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đăng ký tài khoản thành công. Bạn có thể đăng nhập ngay.",
        data={"userId": 1, "username": username}
    )

# UC23: Đăng nhập
@router.post("/login")
async def login(payload: RequestPayload):
    return build_response(
        action="AUTH_LOGIN",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đăng nhập thành công",
        data={
            "userId": 1,
            "displayName": "Người Dùng Hệ Thống",
            "token": "eyJhbGciOiJIUzI1Ni..."
        }
    )

# UC24: Đăng xuất
@router.post("/logout")
async def logout(payload: RequestPayload, authorization: Optional[str] = Header(None)):
    # Đăng xuất yêu cầu truyền Header Authorization
    return build_response(
        action="AUTH_LOGOUT",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Đã đăng xuất thành công.",
        data=None
    )