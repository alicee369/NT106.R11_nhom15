--------------------------------------------------
### UC1: Chạy, Tạm dừng, Tiếp tục và Dừng đồng hồ Pomodoro
- URL Endpoint (Start): /api/pomodoro/start
- URL Endpoint (Pause): /api/pomodoro/pause
- URL Endpoint (Resume): /api/pomodoro/resume
- URL Endpoint (Stop): /api/pomodoro/stop
- Method: POST
- Header: Authorization: Bearer <token>
--------------------------------------------------
// Bắt đầu phiên học
    //Client:
{
  "action": "POMODORO_START",
  "requestId": int,
  "data": {
    "planId": int, // Có thể truyền null nếu không gắn kế hoạch
    "focusMinutes": int,
    "breakMinutes": int
  }
}
    //Server:
        //success
{
  "action": "POMODORO_START",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đã bắt đầu phiên học Pomodoro.",
  "data": {
    "sessionId": int,
    "startTime": time
  }
}
        //fail
{
  "action": "POMODORO_START",
  "requestId": int,
  "success": false,
  "errorCode": "POMODORO_ALREADY_RUNNING",
  "message": "Đồng hồ đang chạy, không thể bắt đầu phiên mới.",
  "data": null
}


// Tạm dừng (Pause) 
    //Client:
{
  "action": "POMODORO_PAUSE", 
  "requestId": int,
  "data": { "sessionId": int }
}
    //Server:
        //fail
{
  "action": "POMODORO_PAUSE", 
  "requestId": int,
  "success": false,
  "errorCode": "SESSION_NOT_FOUND",
  "message": "Không tìm thấy phiên học hoặc phiên không ở trạng thái chạy.",
  "data": null
}


// Tiếp tục (Resume)
    //Client:
{
  "action": "POMODORO_RESUME", 
  "requestId": int,
  "data": { "sessionId": int }
}
    //Server:
        //success
{
  "action": "POMODORO_RESUME", 
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đã tiếp tục phiên học.",
  "data": {
    "status": str, // "RUNNING"
    "accumulatedSeconds": int
  }
}


// Dừng/Hoàn thành phiên học
    //Client:
{
  "action": "POMODORO_STOP",
  "requestId": int,
  "data": { "sessionId": int }
}
    //Server:
        //success
{
  "action": "POMODORO_STOP",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đã kết thúc phiên học và lưu thời gian.",
  "data": {
    "plannedDurationSeconds": int,
    "actualDurationSeconds": int,
    "endTime": time,
    "newlyUnlockedBadges": [
      {
        "badgeId": int,
        "badgeName": str,
        "iconUrl": str,
        "description": str,
        "isUnlocked": bool
      }
    ]
  }
}


--------------------------------------------------
### UC2: Đọc và Tùy chỉnh khung giờ Pomodoro
- URL Endpoint (Get): /api/pomodoro/settings/get
- URL Endpoint (Update): /api/pomodoro/settings/update
- Method: POST
--------------------------------------------------
// Lấy cấu hình
    //Client:
{
  "action": "POMODORO_SETTINGS_GET",
  "requestId": int,
  "data": {}
}
    //Server:
        //success
{
  "action": "POMODORO_SETTINGS_GET",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Thành công.",
  "data": {
    "focusMinutes": int,
    "breakMinutes": int
  }
}


// Cập nhật cấu hình
    //Client:
{
  "action": "POMODORO_SETTINGS_UPDATE",
  "requestId": int,
  "data": { "focusMinutes": int, "breakMinutes": int }
}
    //Server:
        //success
{
  "action": "POMODORO_SETTINGS_UPDATE",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Cấu hình được lưu.",
  "data": {
    "focusMinutes": int,
    "breakMinutes": int
  }
}


--------------------------------------------------
### UC3: Đọc và Đồng bộ tùy chọn hiển thị Mini-player
- URL Endpoint (Get): /api/pomodoro/miniplayer/get
- URL Endpoint (Sync): /api/pomodoro/miniplayer/sync
- Method: POST
--------------------------------------------------
// Lấy tùy chọn
    //Client:
{
  "action": "POMODORO_GET_PREFERENCE",
  "requestId": int,
  "data": {}
}
    //Server:
        //success
{
  "action": "POMODORO_GET_PREFERENCE",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Thành công.",
  "data": { "isMiniPlayer": bool }
}


// Đồng bộ tùy chọn
    //Client:
{
  "action": "POMODORO_SYNC_PREFERENCE",
  "requestId": int,
  "data": { "isMiniPlayer": bool }
}
    //Server:
        //success
{
  "action": "POMODORO_SYNC_PREFERENCE",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đã đồng bộ tùy chọn hiển thị.",
  "data": null
}


--------------------------------------------------
### UC4: Xem thời gian biểu
- URL Endpoint: /api/schedule/list
- Method: POST
--------------------------------------------------
// Xem thời gian biểu
    //Client:
{
  "action": "SCHEDULE_GET_LIST",
  "requestId": int,
  "data": {
    "viewMode": str, 
    "startDate": str,
    "endDate": str,
    "timezone": str
  }
}
    //Server:
        //success
{
  "action": "SCHEDULE_GET_LIST",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Thành công.",
  "data": {
    "events": [
      {
        "eventId": int,
        "title": str,
        "eventType": str,
        "startTime": time,
        "endTime": time
      }
    ]
  }
}


--------------------------------------------------
### UC5: Thêm sự kiện lịch
- URL Endpoint: /api/schedule/add
- Method: POST
--------------------------------------------------
// Thêm sự kiện lịch
    //Client:
{
  "action": "SCHEDULE_ADD",
  "requestId": int,
  "data": {
    "title": str,
    "eventType": str, 
    "startTime": time,
    "endTime": time
  }
}
    //Server:
        //fail 
{
  "action": "SCHEDULE_ADD",
  "requestId": int,
  "success": false,
  "errorCode": "SCHEDULE_CONFLICT", 
  "message": "Bị trùng lịch với sự kiện khác.",
  "data": null
}


--------------------------------------------------
### UC6: Sửa sự kiện lịch
- URL Endpoint: /api/schedule/update
- Method: POST
--------------------------------------------------
// Sửa sự kiện lịch
    //Client:
{
  "action": "SCHEDULE_UPDATE",
  "requestId": int,
  "data": {
    "eventId": int,
    "title": str,
    "eventType": str,
    "startTime": time,
    "endTime": time
  }
}
    //Server:
        //fail 
{
  "action": "SCHEDULE_UPDATE",
  "requestId": int,
  "success": false,
  "errorCode": "EVENT_INVALID_DATA",
  "message": "Thời gian hoặc thông tin không hợp lệ.",
  "data": null
}


--------------------------------------------------
### UC7: Xóa sự kiện lịch
- URL Endpoint: /api/schedule/delete
- Method: POST
--------------------------------------------------
// Xóa sự kiện lịch
    //Client:
{
  "action": "SCHEDULE_DELETE",
  "requestId": int,
  "data": { "eventId": int }
}
    //Server:
        //fail
{
  "action": "SCHEDULE_DELETE",
  "requestId": int,
  "success": false,
  "errorCode": "EVENT_NOT_FOUND",
  "message": "Không tìm thấy sự kiện.",
  "data": null
}


--------------------------------------------------
### UC8: Xem danh sách ghi chú
- URL Endpoint: /api/note/list
- Method: POST
--------------------------------------------------
// Xem danh sách ghi chú (Có phân trang)
    //Client:
{
  "action": "NOTE_GET_LIST",
  "requestId": int,
  "data": { "page": int, "limit": int }
}
    //Server:
        //success
{
  "action": "NOTE_GET_LIST",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Thành công.",
  "data": {
    "notes": [
      {
        "noteId": int,
        "title": str,
        "content": str,
        "isTodoList": bool,
        "isDone": bool
      }
    ],
    "totalCount": int,
    "totalPages": int
  }
}


--------------------------------------------------
### UC9: Thêm ghi chú
- URL Endpoint: /api/note/add
- Method: POST
--------------------------------------------------
// Thêm ghi chú
    //Client:
{
  "action": "NOTE_ADD",
  "requestId": int,
  "data": {
    "title": str,
    "content": str,
    "isTodoList": bool
  }
}
    //Server:
        //fail
{
  "action": "NOTE_ADD",
  "requestId": int,
  "success": false,
  "errorCode": "NOTE_EMPTY_CONTENT",
  "message": "Nội dung ghi chú rỗng.",
  "data": null
}


--------------------------------------------------
### UC10: Sửa ghi chú
- URL Endpoint: /api/note/update
- Method: POST
--------------------------------------------------
// Sửa ghi chú
    //Client:
{
  "action": "NOTE_UPDATE",
  "requestId": int,
  "data": {
    "noteId": int,
    "title": str,
    "content": str,
    "isTodoList": bool,
    "isDone": bool
  }
}
    //Server:
        //success
{
  "action": "NOTE_UPDATE",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Cập nhật thành công.",
  "data": {
    "isDeleted": bool
  }
}


--------------------------------------------------
### UC11: Xóa ghi chú
- URL Endpoint: /api/note/delete
- Method: POST
--------------------------------------------------
// Xóa ghi chú
    //Client:
{
  "action": "NOTE_DELETE",
  "requestId": int,
  "data": { "noteId": int }
}


--------------------------------------------------
### UC12: Đọc và Cấu hình hệ thống nhắc nhở
- URL Endpoint (Get): /api/reminder/config/get
- URL Endpoint (Update): /api/reminder/config/update
- Method: POST
--------------------------------------------------
// Lấy cấu hình 
    //Client:
{
  "action": "REMINDER_CONFIG_GET",
  "requestId": int,
  "data": {}
}
    //Server:
        //success
{
  "action": "REMINDER_CONFIG_GET",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Thành công.",
  "data": {
    "studyReminder": { "enabled": bool, "notifyBeforeMinutes": int },
    "breakReminder": { "enabled": bool, "notifyBeforeMinutes": int },
    "deadlineReminder": { "enabled": bool, "notifyBeforeMinutes": int }
  }
}


// Cấu hình hệ thống nhắc nhở
    //Client:
{
  "action": "REMINDER_CONFIG_UPDATE",
  "requestId": int,
  "data": {
    "studyReminder": { "enabled": bool, "notifyBeforeMinutes": int },
    "breakReminder": { "enabled": bool, "notifyBeforeMinutes": int },
    "deadlineReminder": { "enabled": bool, "notifyBeforeMinutes": int }
  }
}
    //Server:
        //success
{
  "action": "REMINDER_CONFIG_UPDATE",
  "requestId": int,
  "success": true,
  "errorCode": null,
  "message": "Đã lưu cấu hình nhắc nhở.",
  "data": null
}
