from typing import Callable, Optional
import requests
from PySide6.QtCore import QObject, QThread, Signal

from api_client import ClientPayloadBuilder


class APIWorker(QThread):
    # Signal trả về dict JSON từ Server (cả 200 OK và JSON lỗi nghiệp vụ 401/422)
    response_signal = Signal(dict)

    # Signal trả về chuỗi thông báo lỗi khi mất mạng, timeout hoặc server sập
    error_signal = Signal(str)

    # Signal riêng khi HTTP 401 (hết hạn / sai token) để UI điều hướng về đăng nhập
    unauthorized_signal = Signal(dict)

    def __init__(
        self,
        url: str,
        payload: dict,
        headers: Optional[dict] = None,
        timeout: int = 60,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.url = url
        self.payload = payload
        self.headers = headers if headers else {"Content-Type": "application/json"}
        self.timeout = timeout

    def run(self):
        try:
            response = requests.post(
                self.url,
                json=self.payload,
                headers=self.headers,
                timeout=self.timeout,
            )

            # Thử đọc JSON trước (vì Server trả chuẩn JSON cho cả 200, 401, 422)
            body = None
            try:
                body = response.json()
            except ValueError:
                body = None

            if response.status_code == 401:
                err_payload = (
                    body
                    if isinstance(body, dict)
                    else {
                        "action": self.payload.get("action", "UNKNOWN"),
                        "requestId": self.payload.get("requestId", 0),
                        "success": False,
                        "errorCode": "UNAUTHORIZED",
                        "message": "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.",
                        "data": None,
                    }
                )
                self.unauthorized_signal.emit(err_payload)
                self.response_signal.emit(err_payload)
                return

            if response.status_code == 422 and isinstance(body, dict):
                self.response_signal.emit(body)
                return

            response.raise_for_status()

            if not isinstance(body, dict):
                self.error_signal.emit("Dữ liệu phản hồi từ máy chủ không đúng định dạng JSON.")
                return

            self.response_signal.emit(body)

        except requests.exceptions.ConnectionError:
            self.error_signal.emit("Mất kết nối mạng hoặc không thể kết nối đến máy chủ.")
        except requests.exceptions.Timeout:
            self.error_signal.emit("Máy chủ không phản hồi (Timeout). Đã hủy thao tác hiện tại.")
        except requests.exceptions.RequestException as e:
            self.error_signal.emit(f"Lỗi gọi API: {str(e)}")


class APIRequestManager(QObject):
    """
    Quản lý nhiều QThread chạy song song an toàn cho giao diện PySide6.
    Tránh lỗi 'QThread: Destroyed while thread is still running' khi đồng hồ Pomodoro
    đang đếm ngược và người dùng gọi liên tiếp nhiều API (Pause/Stop/Sync/Note...).
    """

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._active_workers: list[APIWorker] = []

    def send(
        self,
        payload: dict,
        token: Optional[str] = None,
        on_response: Optional[Callable[[dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_unauthorized: Optional[Callable[[dict], None]] = None,
        url: Optional[str] = None,
        timeout: int = 60,
    ) -> APIWorker:
        action = payload.get("action", "")
        target_url = url if url else ClientPayloadBuilder.get_url(action)
        headers = (
            ClientPayloadBuilder.build_auth_header(token)
            if token
            else {"Content-Type": "application/json"}
        )

        worker = APIWorker(
            url=target_url,
            payload=payload,
            headers=headers,
            timeout=timeout,
            parent=self,
        )

        if on_response:
            worker.response_signal.connect(on_response)
        if on_error:
            worker.error_signal.connect(on_error)
        if on_unauthorized:
            worker.unauthorized_signal.connect(on_unauthorized)

        worker.finished.connect(lambda w=worker: self._cleanup(w))
        self._active_workers.append(worker)
        worker.start()
        return worker

    def _cleanup(self, worker: APIWorker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        worker.deleteLater()