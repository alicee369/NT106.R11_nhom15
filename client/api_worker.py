import requests
from PySide6.QtCore import QThread, Signal


class APIWorker(QThread):
    # Signal trả về dict (dữ liệu JSON) khi request thành công (HTTP 200 OK)
    response_signal = Signal(dict)

    # Signal trả về chuỗi thông báo lỗi khi có sự cố mạng
    error_signal = Signal(str)

    def __init__(self, url: str, payload: dict, headers=None):
        super().__init__()
        self.url = url
        self.payload = payload
        self.headers = headers if headers else {"Content-Type": "application/json"}

    def run(self):
        try:
            # Gửi HTTP POST request theo thiết kế API
            response = requests.post(
                self.url,
                json=self.payload,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()

            # Gửi dữ liệu JSON thu được qua Signal
            self.response_signal.emit(response.json())
#timeout & bắt exception
        except requests.exceptions.ConnectionError:
            self.error_signal.emit("Không thể kết nối đến máy chủ.")
        except requests.exceptions.Timeout:
            self.error_signal.emit("Máy chủ phản hồi quá lâu.")
        except requests.exceptions.RequestException as e:
            self.error_signal.emit(f"Lỗi gọi API: {str(e)}")