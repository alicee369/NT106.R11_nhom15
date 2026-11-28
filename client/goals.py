import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QLineEdit, QSpinBox, QDialog, QFormLayout,
    QProgressBar, QMessageBox, QScrollArea
)

from api_worker import APIWorker
from api_client import ClientPayloadBuilder


class PlanFormDialog(QDialog):
    """Form dùng chung cho UC13 (tạo) và UC14 (chỉnh sửa)."""

    def __init__(self, plan_data=None, parent=None):
        super().__init__(parent)

        self.plan_data = plan_data or {}
        self.is_edit = plan_data is not None

        self.setWindowTitle("Chỉnh sửa kế hoạch" if self.is_edit else "Tạo kế hoạch học tập")
        self.setMinimumWidth(430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel(
            "Cập nhật thông tin kế hoạch" if self.is_edit
            else "Thiết lập kế hoạch học tập"
        )
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("VD: Ôn tập môn Lập trình mạng")

        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 1000000)
        self.target_spin.setSuffix(" phút")
        self.target_spin.setValue(60)

        if self.is_edit:
            self.name_input.setText(str(self.plan_data.get("planName") or ""))
            target = self.plan_data.get("targetMinutes", 60)
            if isinstance(target, (int, float)) and target > 0:
                self.target_spin.setValue(int(target))

        form.addRow("Tên kế hoạch:", self.name_input)
        form.addRow("Mục tiêu học tập:", self.target_spin)
        layout.addLayout(form)

        note = QLabel("Tiến độ học tập sẽ được hệ thống cập nhật dựa trên thời gian Pomodoro.")
        note.setObjectName("mutedText")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Hủy", clicked=self.reject)
        save_btn = QPushButton(
            "Lưu thay đổi" if self.is_edit else "Tạo kế hoạch",
            objectName="primaryButton",
            clicked=self._validate
        )
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def _validate(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self, "Thiếu thông tin",
                "Vui lòng nhập tên kế hoạch."
            )
            self.name_input.setFocus()
            return

        if self.target_spin.value() <= 0:
            QMessageBox.warning(
                self, "Mục tiêu không hợp lệ",
                "Số phút mục tiêu phải lớn hơn 0."
            )
            return

        self.accept()

    def get_form_data(self):
        return {
            "planName": self.name_input.text().strip(),
            "targetMinutes": self.target_spin.value()
        }


class GoalsWindow(QWidget):
    """UC13: Tạo kế hoạch | UC14: Chỉnh sửa | UC15: Xóa kế hoạch."""

    def __init__(self, token: str, parent=None):
        super().__init__(parent)

        self.token = token
        self.workers = []
        self.plans = []

        self._build_ui()
        self._apply_styles()
        self.load_plans()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(5)

        title = QLabel("Mục tiêu & Kế hoạch học tập", objectName="pageTitle")
        subtitle = QLabel(
            "Thiết lập mục tiêu và theo dõi thời gian học tập của bạn.",
            objectName="mutedText"
        )
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton(
            "+ Tạo kế hoạch",
            objectName="primaryButton",
            clicked=self.open_create_dialog
        )
        header.addWidget(self.add_btn)
        root.addLayout(header)

        summary = QFrame(objectName="card")
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(18, 14, 18, 14)

        self.count_label = QLabel("0 kế hoạch")
        self.count_label.setObjectName("summaryValue")
        summary_layout.addWidget(QLabel("Tổng số kế hoạch:"))
        summary_layout.addWidget(self.count_label)
        summary_layout.addStretch()

        self.refresh_btn = QPushButton("Tải lại", clicked=self.load_plans)
        summary_layout.addWidget(self.refresh_btn)
        root.addWidget(summary)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 6, 0)
        self.list_layout.setSpacing(12)
        self.scroll.setWidget(self.list_container)
        root.addWidget(self.scroll, 1)

        self.status_label = QLabel("Đang tải danh sách kế hoạch...", objectName="mutedText")
        root.addWidget(self.status_label)

    def _send_api(self, endpoint, action, data, on_success, on_error=None):
        payload = {
            "action": action,
            "requestId": random.randint(1000, 999999),
            "data": data
        }
        url = f"{ClientPayloadBuilder.BASE_URL}{endpoint}"
        headers = ClientPayloadBuilder.build_auth_header(self.token)

        worker = APIWorker(url, payload, headers)
        self.workers.append(worker)

        def cleanup():
            if worker in self.workers:
                self.workers.remove(worker)

        def handle_response(response):
            cleanup()
            if response.get("success") is not True:
                message = response.get("message") or "Máy chủ không xử lý được yêu cầu."
                QMessageBox.warning(self, "Yêu cầu không thành công", message)
                if on_error:
                    on_error(response)
                return
            on_success(response)

        def handle_error(error_message):
            cleanup()
            QMessageBox.warning(self, "Lỗi kết nối", error_message)
            if on_error:
                on_error({"success": False, "message": error_message})

        worker.response_signal.connect(handle_response)
        worker.error_signal.connect(handle_error)
        worker.finished.connect(cleanup)
        worker.start()

    # UC13/UC14/UC15: lấy danh sách và tiến độ kế hoạch
    def load_plans(self):
        self.status_label.setText("Đang tải danh sách kế hoạch...")
        self.refresh_btn.setEnabled(False)

        def on_loaded(response):
            self.refresh_btn.setEnabled(True)
            data = response.get("data") or {}
            plans = data.get("plans") or []

            if not isinstance(plans, list):
                self.plans = []
                self.status_label.setText("Dữ liệu danh sách kế hoạch không hợp lệ.")
                self._render_plans()
                return

            self.plans = [item for item in plans if isinstance(item, dict)]
            self._render_plans()
            self.status_label.setText(
                f"Đã tải {len(self.plans)} kế hoạch."
                if self.plans else "Bạn chưa có kế hoạch học tập nào."
            )

        def on_failed(_response):
            self.refresh_btn.setEnabled(True)
            self.status_label.setText("Không thể tải danh sách kế hoạch.")

        self._send_api(
            "/api/plan/list",
            "PLAN_GET_LIST",
            {},
            on_loaded,
            on_failed
        )

    def _clear_plan_cards(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_plans(self):
        self._clear_plan_cards()
        self.count_label.setText(f"{len(self.plans)} kế hoạch")

        if not self.plans:
            empty_card = QFrame(objectName="card")
            empty_layout = QVBoxLayout(empty_card)
            empty_layout.setContentsMargins(24, 30, 24, 30)

            empty_title = QLabel("Chưa có kế hoạch học tập")
            empty_title.setObjectName("emptyTitle")
            empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_desc = QLabel(
                "Nhấn “+ Tạo kế hoạch” để thiết lập mục tiêu học tập đầu tiên."
            )
            empty_desc.setObjectName("mutedText")
            empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_desc.setWordWrap(True)

            empty_layout.addWidget(empty_title)
            empty_layout.addWidget(empty_desc)
            self.list_layout.addWidget(empty_card)
            self.list_layout.addStretch()
            return

        for plan in self.plans:
            self.list_layout.addWidget(self._create_plan_card(plan))

        self.list_layout.addStretch()

    def _create_plan_card(self, plan):
        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 17, 20, 17)
        layout.setSpacing(11)

        top = QHBoxLayout()
        name = QLabel(str(plan.get("planName") or "Kế hoạch chưa có tên"))
        name.setObjectName("planName")
        top.addWidget(name)
        top.addStretch()

        edit_btn = QPushButton("Sửa")
        edit_btn.clicked.connect(lambda checked=False, item=plan: self.open_edit_dialog(item))

        delete_btn = QPushButton("Xóa")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(lambda checked=False, item=plan: self.delete_plan(item))

        top.addWidget(edit_btn)
        top.addWidget(delete_btn)
        layout.addLayout(top)

        studied = plan.get("studiedMinutes", 0)
        target = plan.get("targetMinutes", 0)
        percent = plan.get("progressPercent", 0)

        try:
            studied = max(0, int(studied))
        except (TypeError, ValueError):
            studied = 0

        try:
            target = max(0, int(target))
        except (TypeError, ValueError):
            target = 0

        try:
            percent = float(percent)
        except (TypeError, ValueError):
            percent = 0.0

        percent = max(0.0, min(100.0, percent))

        info = QHBoxLayout()
        info.addWidget(QLabel(f"Đã học: {studied} phút"))
        info.addStretch()
        info.addWidget(QLabel(f"Mục tiêu: {target} phút"))
        info.addStretch()
        percent_label = QLabel(f"{percent:.1f}%")
        percent_label.setObjectName("progressValue")
        info.addWidget(percent_label)
        layout.addLayout(info)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(round(percent))
        progress.setFormat("%p%")
        progress.setTextVisible(True)
        layout.addWidget(progress)

        return card

    # UC13: tạo kế hoạch mới
    def open_create_dialog(self):
        dialog = PlanFormDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.add_btn.setEnabled(False)
        form_data = dialog.get_form_data()

        def on_created(response):
            self.add_btn.setEnabled(True)
            QMessageBox.information(
                self, "Thành công",
                response.get("message") or "Đã tạo kế hoạch học tập."
            )
            self.load_plans()

        def on_failed(_response):
            self.add_btn.setEnabled(True)

        self._send_api(
            "/api/plan/create",
            "PLAN_CREATE",
            form_data,
            on_created,
            on_failed
        )

    # UC14: chỉnh sửa kế hoạch
    def open_edit_dialog(self, plan):
        plan_id = plan.get("planId")
        if plan_id is None:
            QMessageBox.warning(self, "Lỗi dữ liệu", "Kế hoạch không có planId.")
            return

        dialog = PlanFormDialog(plan_data=plan, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload_data = {"planId": plan_id, **dialog.get_form_data()}

        def on_updated(response):
            QMessageBox.information(
                self, "Thành công",
                response.get("message") or "Đã cập nhật kế hoạch."
            )
            self.load_plans()

        self._send_api(
            "/api/plan/update",
            "PLAN_UPDATE",
            payload_data,
            on_updated
        )

    # UC15: xác nhận trước khi xóa kế hoạch
    def delete_plan(self, plan):
        plan_id = plan.get("planId")
        if plan_id is None:
            QMessageBox.warning(self, "Lỗi dữ liệu", "Kế hoạch không có planId.")
            return

        plan_name = str(plan.get("planName") or "kế hoạch này")
        confirm = QMessageBox.question(
            self,
            "Xác nhận xóa kế hoạch",
            f"Bạn có chắc chắn muốn xóa “{plan_name}” không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        def on_deleted(response):
            QMessageBox.information(
                self, "Thành công",
                response.get("message") or "Đã xóa kế hoạch học tập."
            )
            self.load_plans()

        self._send_api(
            "/api/plan/delete",
            "PLAN_DELETE",
            {"planId": plan_id},
            on_deleted
        )

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0B1020;
                color: #F1F5F9;
                font-size: 14px;
            }
            QLabel { background: transparent; }
            QLabel#pageTitle {
                color: #F8FAFC;
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#mutedText {
                color: #94A3B8;
                font-size: 12px;
            }
            QLabel#dialogTitle {
                color: #F8FAFC;
                font-size: 19px;
                font-weight: bold;
            }
            QLabel#summaryValue, QLabel#progressValue {
                color: #C4B5FD;
                font-weight: bold;
            }
            QLabel#planName {
                color: #F8FAFC;
                font-size: 17px;
                font-weight: bold;
            }
            QLabel#emptyTitle {
                color: #E2E8F0;
                font-size: 18px;
                font-weight: bold;
            }
            QFrame#card {
                background-color: #171D2E;
                border: 1px solid #28334B;
                border-radius: 13px;
            }
            QLineEdit, QSpinBox {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #35415A;
                border-radius: 7px;
                padding: 8px 10px;
            }
            QProgressBar {
                background-color: #0F172A;
                color: #FFFFFF;
                border: 1px solid #35415A;
                border-radius: 7px;
                text-align: center;
                min-height: 17px;
            }
            QProgressBar::chunk {
                background-color: #7C3AED;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #263248;
                color: #E2E8F0;
                border: 1px solid #35415A;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #35435D; }
            QPushButton:disabled {
                color: #64748B;
                background-color: #1E293B;
            }
            QPushButton#primaryButton {
                background-color: #6D3CCB;
                border: 1px solid #8055D9;
                color: #FFFFFF;
            }
            QPushButton#primaryButton:hover { background-color: #8055D9; }
            QPushButton#dangerButton {
                background-color: #7F1D1D;
                border: 1px solid #991B1B;
                color: #FFFFFF;
            }
        """)
