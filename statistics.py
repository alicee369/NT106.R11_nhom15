from datetime import datetime
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from api_client import ClientPayloadBuilder
from api_worker import APIRequestManager


class BarChartWidget(QWidget):
    """Biểu đồ cột vẽ bằng QPainter cho dữ liệu chartData của UC16."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._items: list[dict] = []
        self.setMinimumHeight(230)

    def set_data(self, items: list[dict]):
        self._items = items if isinstance(items, list) else []
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(44, 24, -18, -38)
        if rect.width() <= 20 or rect.height() <= 20:
            return

        # Trục cơ sở
        painter.setPen(QPen(QColor("#35415A"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        if not self._items:
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                "Chưa có dữ liệu thời gian học. Hãy bắt đầu một phiên Pomodoro!",
            )
            return

        minutes_list = [max(0.0, float(x.get("studyMinutes") or 0)) for x in self._items]
        max_val = max(minutes_list) if minutes_list else 0.0
        max_val = max(max_val, 1.0)

        n = len(self._items)
        slot_w = rect.width() / n
        bar_w = max(14.0, min(52.0, slot_w * 0.55))

        for idx, item in enumerate(self._items):
            mins = max(0.0, float(item.get("studyMinutes") or 0))
            label = str(item.get("label") or "")
            tag = item.get("subjectTag")

            bar_h = (mins / max_val) * (rect.height() - 16)
            x = rect.left() + idx * slot_w + (slot_w - bar_w) / 2
            y = rect.bottom() - bar_h

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#7C3AED"))
            painter.drawRoundedRect(x, y, bar_w, bar_h, 5, 5)

            # Giá trị phút trên đầu cột
            painter.setPen(QColor("#E2E8F0"))
            painter.drawText(
                int(x - 10),
                int(y - 18),
                int(bar_w + 20),
                16,
                Qt.AlignmentFlag.AlignCenter,
                f"{int(mins)}m",
            )

            # Nhãn trục hoành
            display_lbl = f"{label}\n({tag})" if tag else label
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(
                int(x - 16),
                rect.bottom() + 4,
                int(slot_w + 32),
                32,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                display_lbl,
            )


class StatisticsWindow(QWidget):
    """Trang Thống kê - GPA: UC16 (Biểu đồ thống kê) & UC18 (Ước lượng GPA)."""

    def __init__(self, token: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.token = token
        self.req_manager = APIRequestManager(self)
        self.score_rows: list[dict] = []

        self._build_ui()
        self._apply_styles()
        self.add_score_row(0.0, 30.0)
        self.load_chart()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # --- KHU VỰC 1: UC16 THỐNG KÊ TRỰC QUAN ---
        uc16_card = QFrame(objectName="card")
        uc16_layout = QVBoxLayout(uc16_card)
        uc16_layout.setContentsMargins(22, 18, 22, 18)
        uc16_layout.setSpacing(14)

        header_16 = QHBoxLayout()
        header_16.addWidget(QLabel("Thống kê thời gian học (UC16)", objectName="sectionTitle"))
        header_16.addStretch()
        self.total_minutes_label = QLabel("Tổng: 0 phút", objectName="badgeValue")
        header_16.addWidget(self.total_minutes_label)
        uc16_layout.addLayout(header_16)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        filter_row.addWidget(QLabel("Khoảng thời gian:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Ngày (DAY)", "DAY")
        self.filter_combo.addItem("Tuần (WEEK)", "WEEK")
        self.filter_combo.addItem("Tháng (MONTH)", "MONTH")
        self.filter_combo.setCurrentIndex(1)
        filter_row.addWidget(self.filter_combo)

        filter_row.addWidget(QLabel("Môn học (subjectTag):"))
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Để trống = lấy tổng (VD: Toán)")
        filter_row.addWidget(self.subject_input)

        self.refresh_chart_btn = QPushButton(
            "Xem thống kê", objectName="primaryButton", clicked=self.load_chart
        )
        filter_row.addWidget(self.refresh_chart_btn)
        uc16_layout.addLayout(filter_row)

        self.chart_widget = BarChartWidget()
        uc16_layout.addWidget(self.chart_widget)

        self.chart_status = QLabel("Đang tải dữ liệu thống kê...", objectName="mutedText")
        uc16_layout.addWidget(self.chart_status)
        root.addWidget(uc16_card)

        # --- KHU VỰC 2: UC18 ƯỚC LƯỢNG GPA ---
        uc18_card = QFrame(objectName="card")
        uc18_layout = QVBoxLayout(uc18_card)
        uc18_layout.setContentsMargins(22, 18, 22, 18)
        uc18_layout.setSpacing(14)

        uc18_layout.addWidget(QLabel("Ước lượng GPA (UC18)", objectName="sectionTitle"))

        config_grid = QGridLayout()
        config_grid.setHorizontalSpacing(14)
        config_grid.setVerticalSpacing(10)

        self.target_gpa_spin = QDoubleSpinBox()
        self.target_gpa_spin.setRange(0.0, 10.0)
        self.target_gpa_spin.setDecimals(2)
        self.target_gpa_spin.setSingleStep(0.1)
        self.target_gpa_spin.setValue(8.0)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(1.0, 10.0)
        self.scale_spin.setDecimals(1)
        self.scale_spin.setValue(10.0)

        self.remaining_weight_spin = QDoubleSpinBox()
        self.remaining_weight_spin.setRange(0.0, 100.0)
        self.remaining_weight_spin.setDecimals(1)
        self.remaining_weight_spin.setSuffix(" %")
        self.remaining_weight_spin.setValue(50.0)

        config_grid.addWidget(QLabel("GPA mục tiêu (targetGPA):"), 0, 0)
        config_grid.addWidget(self.target_gpa_spin, 0, 1)
        config_grid.addWidget(QLabel("Thang điểm (scale):"), 0, 2)
        config_grid.addWidget(self.scale_spin, 0, 3)
        config_grid.addWidget(QLabel("Tỷ trọng còn lại:"), 1, 0)
        config_grid.addWidget(self.remaining_weight_spin, 1, 1)
        uc18_layout.addLayout(config_grid)

        scores_header = QHBoxLayout()
        scores_header.addWidget(QLabel("Điểm thành phần hiện tại (currentScores)", objectName="subTitle"))
        scores_header.addStretch()
        add_row_btn = QPushButton("+ Thêm dòng điểm", clicked=lambda: self.add_score_row())
        scores_header.addWidget(add_row_btn)
        uc18_layout.addLayout(scores_header)

        self.scores_container = QVBoxLayout()
        self.scores_container.setSpacing(8)
        uc18_layout.addLayout(self.scores_container)

        action_row = QHBoxLayout()
        self.estimate_btn = QPushButton(
            "Tính điểm cần đạt", objectName="primaryButton", clicked=self.estimate_gpa
        )
        action_row.addWidget(self.estimate_btn)
        action_row.addStretch()
        uc18_layout.addLayout(action_row)

        self.result_label = QLabel("Kết quả sẽ hiển thị tại đây.", objectName="resultBox")
        self.result_label.setWordWrap(True)
        uc18_layout.addWidget(self.result_label)

        root.addWidget(uc18_card)
        root.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def add_score_row(self, default_score: float = 0.0, default_weight: float = 10.0):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        score_spin = QDoubleSpinBox()
        score_spin.setRange(0.0, 10.0)
        score_spin.setDecimals(2)
        score_spin.setValue(default_score)

        weight_spin = QDoubleSpinBox()
        weight_spin.setRange(0.0, 100.0)
        weight_spin.setDecimals(1)
        weight_spin.setSuffix(" %")
        weight_spin.setValue(default_weight)

        remove_btn = QPushButton("Xóa", objectName="dangerButton")

        entry = {"widget": row_widget, "score": score_spin, "weight": weight_spin}
        remove_btn.clicked.connect(lambda: self._remove_score_row(entry))

        row_layout.addWidget(QLabel("Điểm:"))
        row_layout.addWidget(score_spin)
        row_layout.addWidget(QLabel("Tỷ trọng:"))
        row_layout.addWidget(weight_spin)
        row_layout.addWidget(remove_btn)
        row_layout.addStretch()

        self.score_rows.append(entry)
        self.scores_container.addWidget(row_widget)

    def _remove_score_row(self, entry: dict):
        if len(self.score_rows) <= 1:
            QMessageBox.information(self, "Lưu ý", "Cần giữ ít nhất 1 dòng điểm thành phần.")
            return
        if entry in self.score_rows:
            self.score_rows.remove(entry)
        widget = entry["widget"]
        self.scores_container.removeWidget(widget)
        widget.deleteLater()

    def load_chart(self):
        filter_type = self.filter_combo.currentData() or "WEEK"
        raw_tag = self.subject_input.text().strip()
        subject_tag = raw_tag if raw_tag else None
        local_tz = datetime.now().astimezone().tzname() or "Asia/Ho_Chi_Minh"

        payload = {
            "action": "STATISTIC_GET_CHART",
            "requestId": ClientPayloadBuilder.next_request_id(),
            "data": {
                "filterType": filter_type,
                "timezone": local_tz,
                "subjectTag": subject_tag,
            },
        }

        self.refresh_chart_btn.setEnabled(False)
        self.chart_status.setText("Đang tải dữ liệu thống kê...")

        def on_res(res: dict):
            self.refresh_chart_btn.setEnabled(True)
            if res.get("success") is not True:
                self.chart_status.setText(res.get("message") or "Không tải được thống kê.")
                QMessageBox.warning(self, "Thông báo", res.get("message") or "Lỗi thống kê.")
                return

            data = res.get("data") or {}
            total_mins = data.get("totalStudyMinutes", 0)
            chart_data = data.get("chartData") or []
            self.total_minutes_label.setText(f"Tổng: {total_mins} phút")
            self.chart_widget.set_data(chart_data)
            self.chart_status.setText(f"Đã cập nhật ({filter_type}).")

        def on_err(err_msg: str):
            self.refresh_chart_btn.setEnabled(True)
            self.chart_status.setText("Đã hủy thao tác do lỗi kết nối.")
            QMessageBox.warning(self, "Lỗi kết nối", err_msg)

        self.req_manager.send(
            payload=payload,
            token=self.token,
            on_response=on_res,
            on_error=on_err,
            url=f"{ClientPayloadBuilder.BASE_URL}/api/statistic/view",
        )

    def estimate_gpa(self):
        current_scores = []
        total_comp_weight = 0.0
        for row in self.score_rows:
            s = float(row["score"].value())
            w = float(row["weight"].value())
            total_comp_weight += w
            current_scores.append({"score": s, "weightPercent": w})

        remaining_w = float(self.remaining_weight_spin.value())
        target_gpa = float(self.target_gpa_spin.value())
        scale = float(self.scale_spin.value())

        if total_comp_weight + remaining_w > 100.0001:
            QMessageBox.warning(
                self,
                "Dữ liệu không hợp lệ",
                "Tổng tỷ trọng điểm thành phần và tỷ trọng còn lại không được vượt quá 100%.",
            )
            return

        payload = {
            "action": "SCORE_ESTIMATE_GPA",
            "requestId": ClientPayloadBuilder.next_request_id(),
            "data": {
                "currentScores": current_scores,
                "remainingWeightPercent": remaining_w,
                "targetGPA": target_gpa,
                "scale": scale,
            },
        }

        self.estimate_btn.setEnabled(False)
        self.result_label.setText("Đang tính toán...")

        def on_res(res: dict):
            self.estimate_btn.setEnabled(True)
            if res.get("success") is not True:
                err_code = res.get("errorCode")
                msg = res.get("message") or "Mục tiêu không khả thi hoặc định dạng sai."
                self.result_label.setText(f"[{err_code or 'ERROR'}] {msg}")
                QMessageBox.warning(self, "Ước lượng GPA", msg)
                return

            data = res.get("data") or {}
            req_score = data.get("requiredScoreForRemainingWeight")
            self.result_label.setText(
                f"Điểm trung bình cần đạt cho phần còn lại: {req_score}"
            )

        def on_err(err_msg: str):
            self.estimate_btn.setEnabled(True)
            self.result_label.setText("Đã hủy tính toán do lỗi kết nối.")
            QMessageBox.warning(self, "Lỗi kết nối", err_msg)

        self.req_manager.send(
            payload=payload,
            token=self.token,
            on_response=on_res,
            on_error=on_err,
            url=f"{ClientPayloadBuilder.BASE_URL}/api/score/estimate",
        )

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #0B1020; color: #F1F5F9; font-size: 14px; }
            QLabel { background: transparent; }
            QLabel#sectionTitle { color: #F8FAFC; font-size: 20px; font-weight: bold; }
            QLabel#subTitle { color: #CBD5E1; font-size: 15px; font-weight: bold; }
            QLabel#badgeValue { color: #C4B5FD; font-weight: bold; }
            QLabel#mutedText { color: #94A3B8; font-size: 12px; }
            QLabel#resultBox {
                background-color: #0F172A; border: 1px solid #35415A;
                border-radius: 8px; padding: 10px 12px; color: #E2E8F0; font-weight: bold;
            }
            QFrame#card {
                background-color: #171D2E; border: 1px solid #28334B; border-radius: 14px;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #0F172A; color: #F8FAFC;
                border: 1px solid #35415A; border-radius: 7px; padding: 7px 10px;
            }
            QPushButton {
                background-color: #263248; color: #E2E8F0;
                border: 1px solid #35415A; border-radius: 8px; padding: 8px 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #35435D; }
            QPushButton#primaryButton {
                background-color: #6D3CCB; border: 1px solid #8055D9; color: #FFFFFF;
            }
            QPushButton#dangerButton {
                background-color: #7F1D1D; border: 1px solid #991B1B; color: #FFFFFF;
            }
        """)