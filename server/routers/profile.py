from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any

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

# UC25: Xem hồ sơ người dùng
@router.post("")
async def get_profile(payload: RequestPayload, authorization: Optional[str] = Header(None)):
    return build_response(
        action="PROFILE_GET",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Lấy thông tin hồ sơ thành công.",
        data={
            "userId": 1,
            "username": "user_account",
            "displayName": "Người Dùng Hệ Thống",
            "joinDate": "2026-10-25T00:00:00Z"
        }
    )

# UC26: Cập nhật thông tin cá nhân
@router.post("/update")
async def update_profile(payload: RequestPayload, authorization: Optional[str] = Header(None)):
    display_name = payload.data.get("displayName")
    return build_response(
        action="PROFILE_UPDATE",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Cập nhật hồ sơ thành công.",
        data={"displayName": display_name}
    )

# UC27: Xóa tài khoản
@router.post("/delete")
async def delete_profile(payload: RequestPayload, authorization: Optional[str] = Header(None)):
    return build_response(
        action="PROFILE_DELETE",
        req_id=payload.requestId,
        success=True,
        error_code=None,
        message="Tài khoản và toàn bộ dữ liệu của bạn đã được xóa vĩnh viễn.",
        data=None
    )