import random
from PySide6.QtCore import Signal 
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QCheckBox, QSpinBox, QGridLayout, QMessageBox
)
from api_worker import APIWorker
from api_client import ClientPayloadBuilder


class RemindersWindow(QWidget):
    """UC12: Đọc (/api/reminder/config/get) và Cập nhật (/api/reminder/config/update) cấu hình nhắc nhở."""
    config_updated = Signal(dict) # Signal phát ra mỗi khi cấu hình được tải hoặc lưu thành công

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.workers: list[APIWorker] = []

        #Lưu cấu hình mặc định trong bộ nhớ
        self.current_config = {
            "studyReminder": {"enabled": False, "notifyBeforeMinutes": 5},
            "breakReminder": {"enabled": False, "notifyBeforeMinutes": 5},
            "deadlineReminder": {"enabled": False, "notifyBeforeMinutes": 30},
        }

        self._build_ui()
        self._apply_styles()
        self.load_config()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        header = QHBoxLayout()
        header.addWidget(QLabel("Hệ thống nhắc nhở", objectName="pageTitle"))
        header.addStretch()
        reload_btn = QPushButton("Tải lại", clicked=self.load_config)
        header.addWidget(reload_btn)
        root.addLayout(header)

        card = QFrame(objectName="card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(18)

        card_layout.addWidget(QLabel("Cấu hình thông báo nhắc nhở", objectName="sectionTitle"))
        card_layout.addWidget(
            QLabel("Bật/tắt từng loại nhắc nhở và thiết lập số phút thông báo trước.", objectName="mutedText")
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(16)

        grid.addWidget(QLabel("Loại nhắc nhở", objectName="colHeader"), 0, 0)
        grid.addWidget(QLabel("Trạng thái", objectName="colHeader"), 0, 1)
        grid.addWidget(QLabel("Báo trước (phút)", objectName="colHeader"), 0, 2)

        self.study_enabled, self.study_minutes = self._add_row(grid, 1, "Nhắc giờ học")
        self.break_enabled, self.break_minutes = self._add_row(grid, 2, "Nhắc nghỉ giải lao")
        self.deadline_enabled, self.deadline_minutes = self._add_row(grid, 3, "Nhắc deadline")

        card_layout.addLayout(grid)

        footer = QHBoxLayout()
        self.status_label = QLabel("Đang tải cấu hình...", objectName="mutedText")
        footer.addWidget(self.status_label)
        footer.addStretch()

        self.save_btn = QPushButton("Lưu cấu hình", objectName="primaryButton", clicked=self.save_config)
        footer.addWidget(self.save_btn)
        card_layout.addLayout(footer)

        root.addWidget(card)
        root.addStretch()

    def _add_row(self, grid: QGridLayout, row: int, label_text: str) -> tuple[QCheckBox, QSpinBox]:
        lbl = QLabel(label_text)
        chk = QCheckBox("Bật")
        spin = QSpinBox()
        spin.setRange(0, 1440)
        spin.setSuffix(" phút")

        chk.toggled.connect(spin.setEnabled)
        spin.setEnabled(chk.isChecked())

        grid.addWidget(lbl, row, 0)
        grid.addWidget(chk, row, 1)
        grid.addWidget(spin, row, 2)
        return chk, spin

    def _send_api(self, endpoint: str, action: str, data: dict, on_success, on_error=None):
        payload = {
            "action": action,
            "requestId": random.randint(1000, 999999),
            "data": data,
        }
        url = f"{ClientPayloadBuilder.BASE_URL}{endpoint}"
        headers = ClientPayloadBuilder.build_auth_header(self.token)

        worker = APIWorker(url, payload, headers)
        self.workers.append(worker)

        def cleanup():
            if worker in self.workers:
                self.workers.remove(worker)

        def handle_response(res: dict):
            cleanup()
            if res.get("success") is not True:
                QMessageBox.warning(self, "Thông báo", res.get("message") or "Máy chủ không xử lý được yêu cầu.")
                if on_error:
                    on_error(res)
                return
            on_success(res)

        def handle_error(err_msg: str):
            cleanup()
            QMessageBox.warning(self, "Lỗi kết nối", err_msg)
            if on_error:
                on_error({"success": False, "message": err_msg})

        worker.response_signal.connect(handle_response)
        worker.error_signal.connect(handle_error)
        worker.start()

    def load_config(self):
        self.status_label.setText("Đang đọc cấu hình nhắc nhở...")

        def on_loaded(res: dict):
            data = res.get("data") or {}
            self._apply_item(data.get("studyReminder"), self.study_enabled, self.study_minutes, default_min=5)
            self._apply_item(data.get("breakReminder"), self.break_enabled, self.break_minutes, default_min=5)
            self._apply_item(data.get("deadlineReminder"), self.deadline_enabled, self.deadline_minutes, default_min=30)
            
            self._sync_local_config() # cập nhật cache, phát signal đồng bộ
            self.status_label.setText("Đã đồng bộ cấu hình từ máy chủ.")

        self._send_api(
            "/api/reminder/config/get",
            "REMINDER_CONFIG_GET",
            {},
            on_loaded,
            lambda _: self.status_label.setText("Không tải được cấu hình nhắc nhở."),
        )

    @staticmethod
    def _apply_item(item: dict | None, chk: QCheckBox, spin: QSpinBox, default_min: int):
        if not isinstance(item, dict):
            return
        enabled = bool(item.get("enabled", False))
        minutes = int(item.get("notifyBeforeMinutes", default_min))
        chk.setChecked(enabled)
        spin.setValue(max(0, minutes))
        spin.setEnabled(enabled)

    def save_config(self):
        payload_data = {
            "studyReminder": {
                "enabled": self.study_enabled.isChecked(),
                "notifyBeforeMinutes": int(self.study_minutes.value()),
            },
            "breakReminder": {
                "enabled": self.break_enabled.isChecked(),
                "notifyBeforeMinutes": int(self.break_minutes.value()),
            },
            "deadlineReminder": {
                "enabled": self.deadline_enabled.isChecked(),
                "notifyBeforeMinutes": int(self.deadline_minutes.value()),
            },
        }

        self.save_btn.setEnabled(False)

        def on_saved(res: dict):
            self.save_btn.setEnabled(True)
            self._sync_local_config() # Cập nhật cache và phát tín hiệu đồng bộ ngay khi bấm Lưu
            self.status_label.setText("Đã lưu cấu hình nhắc nhở.")
            QMessageBox.information(self, "Thành công", res.get("message") or "Đã lưu cấu hình nhắc nhở.")

        self._send_api(
            "/api/reminder/config/update",
            "REMINDER_CONFIG_UPDATE",
            payload_data,
            on_saved,
            lambda _: self.save_btn.setEnabled(True),
        )

    # Hàm gom cấu hình hiện tại trên giao diện và phát Signal
    def _sync_local_config(self):
        self.current_config = {
            "studyReminder": {
                "enabled": self.study_enabled.isChecked(),
                "notifyBeforeMinutes": int(self.study_minutes.value()),
            },
            "breakReminder": {
                "enabled": self.break_enabled.isChecked(),
                "notifyBeforeMinutes": int(self.break_minutes.value()),
            },
            "deadlineReminder": {
                "enabled": self.deadline_enabled.isChecked(),
                "notifyBeforeMinutes": int(self.deadline_minutes.value()),
            },
        }
        self.config_updated.emit(self.current_config)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #0B1020; color: #F1F5F9; font-size: 14px; }
            QLabel { background: transparent; }
            QLabel#pageTitle { color: #F8FAFC; font-size: 24px; font-weight: bold; }
            QLabel#sectionTitle { color: #F8FAFC; font-size: 18px; font-weight: bold; }
            QLabel#colHeader { color: #A78BFA; font-size: 12px; font-weight: bold; }
            QLabel#mutedText { color: #94A3B8; font-size: 12px; }
            QFrame#card { background-color: #171D2E; border: 1px solid #28334B; border-radius: 14px; }
            QSpinBox {
                background-color: #0F172A; color: #F8FAFC;
                border: 1px solid #35415A; border-radius: 7px; padding: 7px 10px; min-width: 110px;
            }
            QPushButton {
                background-color: #263248; color: #E2E8F0;
                border: 1px solid #35415A; border-radius: 8px; padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #35435D; }
            QPushButton#primaryButton { background-color: #6D3CCB; border: 1px solid #8055D9; color: #FFFFFF; }
            QPushButton#primaryButton:hover { background-color: #8055D9; }
        """)