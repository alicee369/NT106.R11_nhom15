class ClientPayloadBuilder:
    """Class hỗ trợ tạo cấu trúc JSON chuẩn trước khi đưa vào QThread"""

    @staticmethod
    def build_register_payload(req_id: int, username: str, password: str, display_name: str) -> dict:
        return {
            "action": "AUTH_REGISTER",
            "requestId": req_id,
            "data": {
                "username": username,
                "password": password,
                "displayName": display_name
            }
        }

    @staticmethod
    def build_login_payload(req_id: int, username: str, password: str) -> dict:
        return {
            "action": "AUTH_LOGIN",
            "requestId": req_id,
            "data": {
                "username": username,
                "password": password
            }
        }

    @staticmethod
    def build_auth_header(token: str) -> dict:
        """Dùng cho UC24, UC25, UC26, UC27 yêu cầu Header có Bearer Token"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

    @staticmethod
    def build_profile_update_payload(req_id: int, display_name: str, old_password: str, new_password: str) -> dict:
        return {
            "action": "PROFILE_UPDATE",
            "requestId": req_id,
            "data": {
                "displayName": display_name,
                "oldPassword": old_password,
                "newPassword": new_password
            }
        }