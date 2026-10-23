# Tài liệu API - Ứng dụng Quản lý học tập NT106

--------------------------------------------------
### UC22: Tạo tài khoản
- URL Endpoint: /api/auth/register
- Method: POST
- Header: Không
--------------------------------------------------
//Tạo tk
    //Client:
{
  "action": "AUTH_REGISTER",
  "requestId": int,
  "data": {
    "username": str,
    "password": str,
    "displayName": str 
  }
}
    //Server:
        //success
{
  "action": "AUTH_REGISTER",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đăng ký tài khoản thành công. Bạn có thể đăng nhập ngay.",
  "data": {
    "userId": int,
    "username": str
  }
}
        //fail
{
  "action": "AUTH_REGISTER",
  "requestId": int,
  "success": false,
  "errorCode": "AUTH_USERNAME_EXISTS",
  "message": "Tên đăng nhập này đã có người sử dụng. Vui lòng chọn tên khác.",
  "data": null
}

--------------------------------------------------
### UC23: Đăng nhập
- URL Endpoint: /api/auth/login
- Method: POST
- Header: Không
--------------------------------------------------
//Đăng nhập:
    //Client:
{
  "action": "AUTH_LOGIN",
  "requestId": int,
  "data": {
    "username": str,
    "password": str
  }
}
    //Server
        //success:
{
  "action": "AUTH_LOGIN",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đăng nhập thành công",
  "data": {
    "userId": int,
    "displayName": str,
    "token": "eyJhbGciOiJIUzI1Ni..." 
  }
}
        //fail
{
  "action": "AUTH_LOGIN",
  "requestId": int,
  "success": false,
  "errorCode": "AUTH_INVALID_CREDENTIALS",
  "message": "Tên đăng nhập hoặc mật khẩu không chính xác.",
  "data": null
}

--------------------------------------------------
### UC24: Đăng xuất
- URL Endpoint: /api/auth/logout
- Method: POST
- Header: Authorization: Bearer <token>
--------------------------------------------------
//Đăng xuất
    //Client:
{
  "action": "AUTH_LOGOUT",
  "requestId": int,
  "data": {}
}
    //Server
{
  "action": "AUTH_LOGOUT",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đã đăng xuất thành công.",
  "data": null
}

--------------------------------------------------
### UC25: Xem hồ sơ người dùng
- URL Endpoint: /api/profile
- Method: POST
- Header: Authorization: Bearer <token>
--------------------------------------------------
//Xem hồ sơ người dùng
    //Client
{
  "action": "PROFILE_GET",
  "requestId": int,
  "data": {}
}
    //Server:
{
  "action": "PROFILE_GET",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Lấy thông tin hồ sơ thành công.",
  "data": {
    "userId": int,
    "username": str,
    "displayName": str,
    "joinDate": time
  }
}

--------------------------------------------------
### UC26: Cập nhật thông tin cá nhân
- URL Endpoint: /api/profile/update
- Method: POST
- Header: Authorization: Bearer <token>
--------------------------------------------------
//Update thông tin cá nhân
    //Client
{
  "action": "PROFILE_UPDATE",
  "requestId": int,
  "data": {
    "displayName": str,
    "oldPassword": str, 
    "newPassword": str 
  }
}
    //Server:
        //success
{
  "action": "PROFILE_UPDATE",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Cập nhật hồ sơ thành công.",
  "data": {
    "displayName": str
  }
}
        //fail
{
  "action": "PROFILE_UPDATE",
  "requestId": int,
  "success": false,
  "errorCode": "PROFILE_WRONG_OLD_PASSWORD",
  "message": "Mật khẩu cũ không chính xác. Không thể đổi mật khẩu mới.",
  "data": null
}

--------------------------------------------------
### UC27: Xóa tài khoản
- URL Endpoint: /api/profile/delete
- Method: POST
- Header: Authorization: Bearer <token>
--------------------------------------------------
//Xóa tài khoản
    //Client:
{
  "action": "PROFILE_DELETE",
  "requestId": int,
  "data": {
    "passwordToConfirm": str
  }
}
    //Success
{
  "action": "PROFILE_DELETE",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Tài khoản và toàn bộ dữ liệu của bạn đã được xóa vĩnh viễn.",
  "data": null
}