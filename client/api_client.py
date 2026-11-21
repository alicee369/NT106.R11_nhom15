import itertools
from typing import Optional


class ClientPayloadBuilder:
    """Class hỗ trợ tạo cấu trúc JSON chuẩn và URL trước khi đưa vào QThread"""
    BASE_URL = "https://nt106-r11-nhom15.onrender.com"
    _req_counter = itertools.count(1000)

    ENDPOINTS = {
        # Auth & Profile (giữ nguyên)
        "AUTH_REGISTER": "/api/auth/register",
        "AUTH_LOGIN": "/api/auth/login",
        "AUTH_LOGOUT": "/api/auth/logout",
        "PROFILE_GET": "/api/profile",
        "PROFILE_UPDATE": "/api/profile/update",
        "PROFILE_DELETE": "/api/profile/delete",
        # UC1 - UC3: Pomodoro
        "POMODORO_START": "/api/pomodoro/start",
        "POMODORO_PAUSE": "/api/pomodoro/pause",
        "POMODORO_RESUME": "/api/pomodoro/resume",
        "POMODORO_STOP": "/api/pomodoro/stop",
        "POMODORO_SETTINGS_GET": "/api/pomodoro/settings/get",
        "POMODORO_SETTINGS_UPDATE": "/api/pomodoro/settings/update",
        "POMODORO_GET_PREFERENCE": "/api/pomodoro/miniplayer/get",
        "POMODORO_SYNC_PREFERENCE": "/api/pomodoro/miniplayer/sync",
        # UC4 - UC7: Schedule
        "SCHEDULE_GET_LIST": "/api/schedule/list",
        "SCHEDULE_ADD": "/api/schedule/add",
        "SCHEDULE_UPDATE": "/api/schedule/update",
        "SCHEDULE_DELETE": "/api/schedule/delete",
        # UC8 - UC11: Note
        "NOTE_GET_LIST": "/api/note/list",
        "NOTE_ADD": "/api/note/add",
        "NOTE_UPDATE": "/api/note/update",
        "NOTE_DELETE": "/api/note/delete",
        # UC12: Reminder
        "REMINDER_CONFIG_GET": "/api/reminder/config/get",
        "REMINDER_CONFIG_UPDATE": "/api/reminder/config/update",
    }

    @classmethod
    def next_request_id(cls) -> int:
        return next(cls._req_counter)

    @classmethod
    def get_url(cls, action: str) -> str:
        return f"{cls.BASE_URL}{cls.ENDPOINTS[action]}"

    @staticmethod
    def build_auth_header(token: str) -> dict:
        """Dùng cho mọi API cần Header có Bearer Token (UC1-UC12, UC24-UC27)"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    # --- Auth & Profile (giữ nguyên cho login.py / register.py / profile.py) ---
    @staticmethod
    def build_register_payload(
        req_id: int, username: str, password: str, display_name: str
    ) -> dict:
        return {
            "action": "AUTH_REGISTER",
            "requestId": req_id,
            "data": {
                "username": username,
                "password": password,
                "displayName": display_name,
            },
        }

    @staticmethod
    def build_login_payload(req_id: int, username: str, password: str) -> dict:
        return {
            "action": "AUTH_LOGIN",
            "requestId": req_id,
            "data": {
                "username": username,
                "password": password,
            },
        }

    @staticmethod
    def build_profile_update_payload(
        req_id: int, display_name: str, old_password: str, new_password: str
    ) -> dict:
        return {
            "action": "PROFILE_UPDATE",
            "requestId": req_id,
            "data": {
                "displayName": display_name,
                "oldPassword": old_password,
                "newPassword": new_password,
            },
        }

    # --- UC1: Pomodoro Start / Pause / Resume / Stop ---
    @staticmethod
    def build_pomodoro_start_payload(
        req_id: int,
        focus_minutes: int,
        break_minutes: int,
        plan_id: Optional[int] = None,
    ) -> dict:
        return {
            "action": "POMODORO_START",
            "requestId": req_id,
            "data": {
                "planId": plan_id,
                "focusMinutes": focus_minutes,
                "breakMinutes": break_minutes,
            },
        }

    @staticmethod
    def build_pomodoro_pause_payload(req_id: int, session_id: int) -> dict:
        return {
            "action": "POMODORO_PAUSE",
            "requestId": req_id,
            "data": {"sessionId": session_id},
        }

    @staticmethod
    def build_pomodoro_resume_payload(req_id: int, session_id: int) -> dict:
        return {
            "action": "POMODORO_RESUME",
            "requestId": req_id,
            "data": {"sessionId": session_id},
        }

    @staticmethod
    def build_pomodoro_stop_payload(req_id: int, session_id: int) -> dict:
        return {
            "action": "POMODORO_STOP",
            "requestId": req_id,
            "data": {"sessionId": session_id},
        }

    # --- UC2: Pomodoro Settings ---
    @staticmethod
    def build_pomodoro_settings_get_payload(req_id: int) -> dict:
        return {
            "action": "POMODORO_SETTINGS_GET",
            "requestId": req_id,
            "data": {},
        }

    @staticmethod
    def build_pomodoro_settings_update_payload(
        req_id: int, focus_minutes: int, break_minutes: int
    ) -> dict:
        return {
            "action": "POMODORO_SETTINGS_UPDATE",
            "requestId": req_id,
            "data": {
                "focusMinutes": focus_minutes,
                "breakMinutes": break_minutes,
            },
        }

    # --- UC3: Mini-player ---
    @staticmethod
    def build_miniplayer_get_payload(req_id: int) -> dict:
        return {
            "action": "POMODORO_GET_PREFERENCE",
            "requestId": req_id,
            "data": {},
        }

    @staticmethod
    def build_miniplayer_sync_payload(req_id: int, is_mini_player: bool) -> dict:
        return {
            "action": "POMODORO_SYNC_PREFERENCE",
            "requestId": req_id,
            "data": {"isMiniPlayer": is_mini_player},
        }

    # --- UC4 - UC7: Schedule ---
    @staticmethod
    def build_schedule_list_payload(
        req_id: int,
        view_mode: str,
        start_date: str,
        end_date: str,
        timezone_str: str = "Asia/Ho_Chi_Minh",
    ) -> dict:
        return {
            "action": "SCHEDULE_GET_LIST",
            "requestId": req_id,
            "data": {
                "viewMode": view_mode,
                "startDate": start_date,
                "endDate": end_date,
                "timezone": timezone_str,
            },
        }

    @staticmethod
    def build_schedule_add_payload(
        req_id: int,
        title: str,
        event_type: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> dict:
        return {
            "action": "SCHEDULE_ADD",
            "requestId": req_id,
            "data": {
                "title": title,
                "eventType": event_type,
                "startTime": start_time_iso,
                "endTime": end_time_iso,
            },
        }

    @staticmethod
    def build_schedule_update_payload(
        req_id: int,
        event_id: int,
        title: str,
        event_type: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> dict:
        return {
            "action": "SCHEDULE_UPDATE",
            "requestId": req_id,
            "data": {
                "eventId": event_id,
                "title": title,
                "eventType": event_type,
                "startTime": start_time_iso,
                "endTime": end_time_iso,
            },
        }

    @staticmethod
    def build_schedule_delete_payload(req_id: int, event_id: int) -> dict:
        return {
            "action": "SCHEDULE_DELETE",
            "requestId": req_id,
            "data": {"eventId": event_id},
        }

    # --- UC8 - UC11: Note ---
    @staticmethod
    def build_note_list_payload(req_id: int, page: int = 1, limit: int = 20) -> dict:
        return {
            "action": "NOTE_GET_LIST",
            "requestId": req_id,
            "data": {"page": page, "limit": limit},
        }

    @staticmethod
    def build_note_add_payload(
        req_id: int, title: str, content: str, is_todo_list: bool = False
    ) -> dict:
        return {
            "action": "NOTE_ADD",
            "requestId": req_id,
            "data": {
                "title": title,
                "content": content,
                "isTodoList": is_todo_list,
            },
        }

    @staticmethod
    def build_note_update_payload(
        req_id: int,
        note_id: int,
        title: str,
        content: str,
        is_todo_list: bool,
        is_done: bool,
    ) -> dict:
        return {
            "action": "NOTE_UPDATE",
            "requestId": req_id,
            "data": {
                "noteId": note_id,
                "title": title,
                "content": content,
                "isTodoList": is_todo_list,
                "isDone": is_done,
            },
        }

    @staticmethod
    def build_note_delete_payload(req_id: int, note_id: int) -> dict:
        return {
            "action": "NOTE_DELETE",
            "requestId": req_id,
            "data": {"noteId": note_id},
        }

    # --- UC12: Reminder ---
    @staticmethod
    def build_reminder_get_payload(req_id: int) -> dict:
        return {
            "action": "REMINDER_CONFIG_GET",
            "requestId": req_id,
            "data": {},
        }

    @staticmethod
    def build_reminder_update_payload(
        req_id: int,
        study_enabled: bool,
        study_minutes: int,
        break_enabled: bool,
        break_minutes: int,
        deadline_enabled: bool,
        deadline_minutes: int,
    ) -> dict:
        return {
            "action": "REMINDER_CONFIG_UPDATE",
            "requestId": req_id,
            "data": {
                "studyReminder": {
                    "enabled": study_enabled,
                    "notifyBeforeMinutes": study_minutes,
                },
                "breakReminder": {
                    "enabled": break_enabled,
                    "notifyBeforeMinutes": break_minutes,
                },
                "deadlineReminder": {
                    "enabled": deadline_enabled,
                    "notifyBeforeMinutes": deadline_minutes,
                },
            },
        }