from typing import Any, Dict, List, Optional, Set

import requests
from PySide6.QtCore import QObject, QThread, Signal

try:
    from client.api_client import ClientPayloadBuilder
except ImportError:
    from api_client import ClientPayloadBuilder


class GamificationAPIWorker(QThread):
    """
    QThread bọc requests.post cho Cụm 2 (UC13 - UC16, UC18).
    Chạy hoàn toàn trên luồng nền để không làm đơ UI khi tải biểu đồ hoặc tính GPA.
    """

    # Phát về (action, full_response_dict) khi server trả success=True
    succeeded = Signal(str, dict)
    # Phát về (action, error_code, error_message) khi lỗi nghiệp vụ, mất mạng hoặc timeout
    failed = Signal(str, str, str)

    def __init__(
        self,
        action: str,
        payload: Dict[str, Any],
        token: str,
        timeout: int = 60,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.action = action
        self.payload = payload
        self.token = token
        self.timeout = timeout

    def run(self) -> None:
        try:
            url = ClientPayloadBuilder.get_url(self.action)
            headers = ClientPayloadBuilder.build_auth_header(self.token)

            resp = requests.post(
                url,
                json=self.payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            self.failed.emit(
                self.action,
                "NETWORK_TIMEOUT",
                "Máy chủ không phản hồi (Timeout). Thao tác hiện tại đã được hủy.",
            )
            return
        except requests.exceptions.ConnectionError:
            self.failed.emit(
                self.action,
                "NETWORK_ERROR",
                "Mất kết nối mạng hoặc không thể kết nối máy chủ. Thao tác đã được hủy.",
            )
            return
        except requests.exceptions.RequestException as exc:
            self.failed.emit(
                self.action,
                "NETWORK_ERROR",
                f"Lỗi kết nối mạng: {exc}",
            )
            return

        # Phân tích JSON phản hồi (bảo vệ trường hợp Render trả trang HTML 502/503 lúc đang khởi động)
        try:
            body = resp.json()
        except ValueError:
            self.failed.emit(
                self.action,
                "SERVER_ERROR",
                f"Máy chủ trả về phản hồi không hợp lệ (HTTP {resp.status_code}). Vui lòng thử lại.",
            )
            return

        # Xử lý HTTP 401 (Token sai / hết hạn theo quy ước chung)
        if resp.status_code == 401:
            error_code = body.get("errorCode") or "TOKEN_EXPIRED"
            message = body.get("message") or "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại."
            self.failed.emit(self.action, str(error_code), str(message))
            return

        # Xử lý HTTP 422 (lỗi validate kiểu dữ liệu đầu vào từ FastAPI)
        if resp.status_code == 422:
            if self.action == "SCORE_ESTIMATE_GPA":
                self.failed.emit(
                    self.action,
                    "SCORE_TARGET_UNACHIEVABLE",
                    "Mục tiêu không khả thi hoặc định dạng sai.",
                )
            else:
                self.failed.emit(
                    self.action,
                    "INVALID_INPUT",
                    "Dữ liệu gửi lên không đúng định dạng yêu cầu.",
                )
            return

        # Xử lý HTTP >= 500
        if resp.status_code >= 500:
            self.failed.emit(
                self.action,
                "SERVER_ERROR",
                "Máy chủ đang gặp sự cố tạm thời. Vui lòng thử lại sau.",
            )
            return

        # Phản hồi HTTP 200 theo hợp đồng JSON chuẩn của nhóm
        if isinstance(body, dict) and body.get("success") is True:
            self.succeeded.emit(self.action, body)
        else:
            error_code = (
                body.get("errorCode") if isinstance(body, dict) else None
            ) or "REQUEST_FAILED"
            message = (
                body.get("message") if isinstance(body, dict) else None
            ) or "Thao tác không thành công."
            self.failed.emit(self.action, str(error_code), str(message))


class GamificationClient(QObject):
    """
    Lớp điều phối 6 API Cụm 2 dành cho tầng UI (Tiên).
    Tự quản lý vòng đời QThread để tránh crash khi gửi nhiều request liên tiếp.
    """

    # Signal chung cho toàn bộ Cụm 2
    loading_changed = Signal(str, bool)      # (action, is_loading)
    request_failed = Signal(str, str, str)   # (action, error_code, message)

    # Signal tách riêng theo từng chức năng để UI nối thẳng không cần if/else
    plan_list_loaded = Signal(list)          # List[dict] plans
    plan_created = Signal(dict)              # dict PlanItem vừa tạo
    plan_updated = Signal(str)               # message thành công
    plan_deleted = Signal(str)               # message thành công
    statistic_loaded = Signal(dict)          # {"totalStudyMinutes": int, "chartData": list}
    score_estimated = Signal(float)          # requiredScoreForRemainingWeight

    def __init__(self, parent: Optional[QObject] = None, timeout: int = 60):
        super().__init__(parent)
        self.timeout = timeout
        self._active_workers: Set[GamificationAPIWorker] = set()

    def _dispatch(self, action: str, payload: Dict[str, Any], token: str) -> GamificationAPIWorker:
        worker = GamificationAPIWorker(
            action=action,
            payload=payload,
            token=token,
            timeout=self.timeout,
            parent=self,
        )
        self._active_workers.add(worker)
        self.loading_changed.emit(action, True)

        worker.succeeded.connect(self._on_worker_succeeded)
        worker.failed.connect(self._on_worker_failed)
        worker.finished.connect(lambda w=worker, act=action: self._cleanup_worker(w, act))

        worker.start()
        return worker

    def _on_worker_succeeded(self, action: str, body: dict) -> None:
        data = body.get("data") or {}
        message = body.get("message") or "Thành công."

        if action == "PLAN_GET_LIST":
            self.plan_list_loaded.emit(data.get("plans", []))
        elif action == "PLAN_CREATE":
            self.plan_created.emit(data)
        elif action == "PLAN_UPDATE":
            self.plan_updated.emit(message)
        elif action == "PLAN_DELETE":
            self.plan_deleted.emit(message)
        elif action == "STATISTIC_GET_CHART":
            self.statistic_loaded.emit(
                {
                    "totalStudyMinutes": int(data.get("totalStudyMinutes", 0)),
                    "chartData": data.get("chartData", []),
                }
            )
        elif action == "SCORE_ESTIMATE_GPA":
            self.score_estimated.emit(float(data.get("requiredScoreForRemainingWeight", 0.0)))

    def _on_worker_failed(self, action: str, error_code: str, message: str) -> None:
        self.request_failed.emit(action, error_code, message)

    def _cleanup_worker(self, worker: GamificationAPIWorker, action: str) -> None:
        self._active_workers.discard(worker)
        self.loading_changed.emit(action, False)
        worker.deleteLater()

    # --- 6 hàm gọi API sẵn cho UI ---

    def fetch_plans(self, token: str) -> GamificationAPIWorker:
        req_id = ClientPayloadBuilder.next_request_id()
        payload = ClientPayloadBuilder.build_plan_list_payload(req_id)
        return self._dispatch("PLAN_GET_LIST", payload, token)

    def create_plan(
        self, token: str, plan_name: str, target_minutes: int
    ) -> GamificationAPIWorker:
        req_id = ClientPayloadBuilder.next_request_id()
        payload = ClientPayloadBuilder.build_plan_create_payload(
            req_id, plan_name, target_minutes
        )
        return self._dispatch("PLAN_CREATE", payload, token)

    def update_plan(
        self, token: str, plan_id: int, plan_name: str, target_minutes: int
    ) -> GamificationAPIWorker:
        req_id = ClientPayloadBuilder.next_request_id()
        payload = ClientPayloadBuilder.build_plan_update_payload(
            req_id, plan_id, plan_name, target_minutes
        )
        return self._dispatch("PLAN_UPDATE", payload, token)

    def delete_plan(self, token: str, plan_id: int) -> GamificationAPIWorker:
        req_id = ClientPayloadBuilder.next_request_id()
        payload = ClientPayloadBuilder.build_plan_delete_payload(req_id, plan_id)
        return self._dispatch("PLAN_DELETE", payload, token)

    def fetch_statistic_chart(
        self,
        token: str,
        filter_type: str = "WEEK",
        timezone_str: str = "Asia/Ho_Chi_Minh",
        subject_tag: Optional[str] = None,
    ) -> GamificationAPIWorker:
        req_id = ClientPayloadBuilder.next_request_id()
        payload = ClientPayloadBuilder.build_statistic_view_payload(
            req_id=req_id,
            filter_type=filter_type,
            timezone_str=timezone_str,
            subject_tag=subject_tag,
        )
        return self._dispatch("STATISTIC_GET_CHART", payload, token)

    def estimate_gpa(
        self,
        token: str,
        current_scores: List[Dict[str, float]],
        remaining_weight_percent: float,
        target_gpa: float,
        scale: float = 10.0,
    ) -> GamificationAPIWorker:
        req_id = ClientPayloadBuilder.next_request_id()
        payload = ClientPayloadBuilder.build_score_estimate_payload(
            req_id=req_id,
            current_scores=current_scores,
            remaining_weight_percent=remaining_weight_percent,
            target_gpa=target_gpa,
            scale=scale,
        )
        return self._dispatch("SCORE_ESTIMATE_GPA", payload, token)
