from datetime import datetime, timezone
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QComboBox, QLineEdit, QScrollArea, QMessageBox,
    QButtonGroup, QStackedWidget, QDoubleSpinBox, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from api_client import ClientPayloadBuilder
from api_worker import APIRequestManager
# ============================================================
# WIDGET BIỂU ĐỒ CỘT TỰ VẼ (không cần matplotlib)
# ============================================================
class BarChartWidget(QWidget):
    """Vẽ bar chart thuần QPainter, màu gradient tím giống theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[str, int]] = []  # [(label, minutes)]
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: list[tuple[str, int]]):
        self._data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        pad_left, pad_right = 48, 20
        pad_top, pad_bottom = 20, 44
        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bottom

        # --- Nền lưới ---
        painter.setPen(QPen(QColor("#28334B"), 1, Qt.PenStyle.DashLine))
        for i in range(5):
            y = pad_top + chart_h * i / 4
            painter.drawLine(pad_left, int(y), w - pad_right, int(y))

        if not self._data:
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "Chưa có dữ liệu — hãy bắt đầu phiên Pomodoro đầu tiên!"
            )
            return

        max_val = max((m for _, m in self._data), default=1) or 1
        bar_count = len(self._data)
        slot = chart_w / max(bar_count, 1)
        bar_w = min(slot * 0.55, 56)

        # --- Trục Y labels ---
        painter.setPen(QColor("#94A3B8"))
        painter.setFont(QFont("Segoe UI", 8))
        for i in range(5):
            y = pad_top + chart_h * i / 4
            val = int(max_val * (4 - i) / 4)
            painter.drawText(0, int(y) - 8, pad_left - 8, 16,
                             Qt.AlignmentFlag.AlignRight, f"{val}p")

        # --- Bars ---
        for idx, (label, minutes) in enumerate(self._data):
            x = pad_left + slot * idx + (slot - bar_w) / 2
            bar_h = chart_h * (minutes / max_val) if max_val else 0
            y = pad_top + chart_h - bar_h

            # Gradient tím
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0.0, QColor("#A78BFA"))
            grad.setColorAt(1.0, QColor("#6D3CCB"))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 6, 6)

            # Giá trị trên đầu cột
            if minutes > 0:
                painter.setPen(QColor("#F8FAFC"))
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.drawText(
                    int(x), int(y) - 18, int(bar_w), 16,
                    Qt.AlignmentFlag.AlignCenter, str(minutes)
                )

            # Label dưới trục X
            painter.setPen(QColor("#94A3B8"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(
                int(pad_left + slot * idx), pad_top + chart_h + 8,
                int(slot), 20,
                Qt.AlignmentFlag.AlignCenter, label
            )


# ============================================================
# WIDGET CARD TÓM TẮT (Summary card)
# ============================================================
class SummaryCard(QFrame):
    def __init__(self, icon: str, title: str, value: str, accent: str = "#A78BFA"):
        super().__init__(objectName="summaryCard")
        self.setStyleSheet(f"""
            QFrame#summaryCard {{
                background-color: #171D2E;
                border: 1px solid #28334B;
                border-radius: 12px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)
        ic = QLabel(icon); ic.setStyleSheet(f"font-size:18px; color:{accent};")
        tt = QLabel(title); tt.setStyleSheet("color:#94A3B8; font-size:12px; font-weight:600;")
        top.addWidget(ic); top.addWidget(tt); top.addStretch()
        lay.addLayout(top)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"color:{accent}; font-size:22px; font-weight:bold;")
        lay.addWidget(self.value_label)

    def set_value(self, v: str):
        self.value_label.setText(v)


# ============================================================
# TRANG THỐNG KÊ (UC16)
# ============================================================
class StatisticPage(QWidget):
    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.api = APIRequestManager(self)
        self.filter_type = "WEEK"
        self.subject_tag: str | None = None
        self.total_minutes = 0
        self._build_ui()
        QTimer.singleShot(0, self.load_chart)

    # ------------------ UI ------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("📊 Thống kê học tập")
        title.setStyleSheet("color:#F8FAFC; font-size:22px; font-weight:bold;")
        sub = QLabel("Tổng hợp thời gian học theo ngày / tuần / tháng")
        sub.setStyleSheet("color:#94A3B8; font-size:12px;")
        hl = QVBoxLayout(); hl.setSpacing(2)
        hl.addWidget(title); hl.addWidget(sub)
        header.addLayout(hl); header.addStretch()
        root.addLayout(header)

        # Filter bar
        filter_bar = QFrame(objectName="filterBar")
        filter_bar.setStyleSheet("""
            QFrame#filterBar {
                background-color:#11182C; border:1px solid #28334B;
                border-radius:10px;
            }
        """)
        fl = QHBoxLayout(filter_bar)
        fl.setContentsMargins(14, 10, 14, 10)
        fl.setSpacing(10)

        fl.addWidget(QLabel("Chế độ xem:"))
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        for key, label in [("DAY", "Ngày"), ("WEEK", "Tuần"), ("MONTH", "Tháng")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("viewBtn", True)
            btn.setChecked(key == self.filter_type)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._on_filter_change(k))
            self.btn_group.addButton(btn)
            fl.addWidget(btn)

        fl.addSpacing(20)
        fl.addWidget(QLabel("Môn học:"))
        self.subject_combo = QComboBox()
        self.subject_combo.addItem("— Tất cả —", None)
        self.subject_combo.currentIndexChanged.connect(self._on_subject_change)
        fl.addWidget(self.subject_combo)

        fl.addStretch()
        self.btn_refresh = QPushButton("🔄 Tải lại")
        self.btn_refresh.setObjectName("primaryBtn")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_chart)
        fl.addWidget(self.btn_refresh)
        root.addWidget(filter_bar)

        # Summary cards
        cards = QHBoxLayout(); cards.setSpacing(12)
        self.card_total = SummaryCard("⏱", "Tổng thời gian", "—", "#A78BFA")
        self.card_avg   = SummaryCard("📈", "Trung bình", "—", "#22D3EE")
        self.card_max   = SummaryCard("🔥", "Cao nhất", "—", "#F59E0B")
        for c in (self.card_total, self.card_avg, self.card_max):
            cards.addWidget(c, 1)
        root.addLayout(cards)

        # Chart card
        chart_card = QFrame()
        chart_card.setStyleSheet(
            "background-color:#171D2E; border:1px solid #28334B; border-radius:14px;")
        chart_lay = QVBoxLayout(chart_card)
        chart_lay.setContentsMargins(18, 16, 18, 18)
        chart_lay.setSpacing(6)

        self.chart_title = QLabel("Biểu đồ thời gian học")
        self.chart_title.setStyleSheet(
            "color:#F8FAFC; font-size:14px; font-weight:bold; border:none;")
        chart_lay.addWidget(self.chart_title)

        self.chart = BarChartWidget()
        chart_lay.addWidget(self.chart, 1)
        root.addWidget(chart_card, 1)

        # Style cho view buttons
        self.setStyleSheet(self.styleSheet() + """
            QPushButton[viewBtn="true"] {
                background-color:#1A243D; border:1px solid #2E3B57;
                border-radius:8px; padding:6px 16px; color:#CBD5E1; font-weight:600;
            }
            QPushButton[viewBtn="true"]:hover { background-color:#232F4D; }
            QPushButton[viewBtn="true"]:checked {
                background-color:#6D3CCB; border-color:#8055D9; color:white;
            }
            QPushButton#primaryBtn {
                background-color:#6D3CCB; border:1px solid #8055D9;
                border-radius:8px; padding:6px 16px; color:white; font-weight:600;
            }
            QPushButton#primaryBtn:hover { background-color:#7C4FE0; }
            QComboBox {
                background-color:#1A243D; border:1px solid #2E3B57;
                border-radius:6px; padding:4px 10px; color:#E2E8F0; min-width:140px;
            }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background-color:#1A243D; color:#E2E8F0;
                selection-background-color:#6D3CCB;
            }
        """)

    # ------------------ Handlers ------------------
    def _on_filter_change(self, key: str):
        self.filter_type = key
        self.load_chart()

    def _on_subject_change(self, idx: int):
        self.subject_tag = self.subject_combo.itemData(idx)
        self.load_chart()

    # ------------------ Load chart ------------------
    def load_chart(self):
        payload = ClientPayloadBuilder.build_statistic_chart_payload(
            req_id=ClientPayloadBuilder.next_request_id(),
            filter_type=self.filter_type,
            timezone_str="Asia/Ho_Chi_Minh",
            subject_tag=self.subject_tag,
        )
        self.btn_refresh.setEnabled(False)
        self.api.send(
            payload=payload,
            token=self.token,
            on_response=self._on_chart_response,
            on_error=self._on_error,
        )

    def _on_chart_response(self, resp: dict):
        self.btn_refresh.setEnabled(True)
        if not resp.get("success"):
            msg = resp.get("message", "Không thể tải thống kê.")
            QMessageBox.warning(self, "Lỗi", msg)
            self.chart.set_data([])
            return

        data = resp.get("data") or {}
        self.total_minutes = data.get("totalStudyMinutes", 0) or 0
        raw = data.get("chartData", []) or []

        # Cập nhật summary
        self.card_total.set_value(self._fmt_minutes(self.total_minutes))
        if raw:
            minutes_list = [item.get("studyMinutes", 0) for item in raw]
            avg = self.total_minutes // len(raw)
            mx = max(minutes_list)
            self.card_avg.set_value(self._fmt_minutes(avg))
            self.card_max.set_value(self._fmt_minutes(mx))
        else:
            self.card_avg.set_value("—")
            self.card_max.set_value("—")

        # Gom nhóm theo label (phòng trường hợp có nhiều subjectTag cùng label)
        agg: dict[str, int] = {}
        subjects: set[str] = set()
        for item in raw:
            lbl = str(item.get("label", ""))
            mins = int(item.get("studyMinutes", 0))
            tag = item.get("subjectTag")
            if tag:
                subjects.add(str(tag))
            agg[lbl] = agg.get(lbl, 0) + mins

        self._refresh_subject_combo(subjects)
        self.chart.set_data(list(agg.items()))

        mode_label = {"DAY": "hôm nay", "WEEK": "tuần này", "MONTH": "tháng này"}[self.filter_type]
        self.chart_title.setText(f"Biểu đồ thời gian học — {mode_label}")

    def _refresh_subject_combo(self, subjects: set[str]):
        current = self.subject_tag
        self.subject_combo.blockSignals(True)
        self.subject_combo.clear()
        self.subject_combo.addItem("— Tất cả —", None)
        for s in sorted(subjects):
            self.subject_combo.addItem(s, s)
        # Giữ selection nếu còn tồn tại
        if current in subjects:
            idx = self.subject_combo.findData(current)
            if idx >= 0:
                self.subject_combo.setCurrentIndex(idx)
        else:
            self.subject_tag = None
            self.subject_combo.setCurrentIndex(0)
        self.subject_combo.blockSignals(False)

    def _on_error(self, msg: str):
        self.btn_refresh.setEnabled(True)
        QMessageBox.warning(self, "Lỗi kết nối", msg)

    @staticmethod
    def _fmt_minutes(m: int) -> str:
        if m is None:
            return "—"
        h, mm = divmod(int(m), 60)
        return f"{h}g {mm:02d}p" if h else f"{mm}p"


# ============================================================
# TRANG GPA (UC18)
# ============================================================
class GPACalculatorPage(QWidget):
    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.api = APIRequestManager(self)
        self._score_rows: list[dict] = []  # [{score_input, weight_input}]
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        title = QLabel("🎯 Ước lượng GPA")
        title.setStyleSheet("color:#F8FAFC; font-size:22px; font-weight:bold;")
        sub = QLabel(
            "Nhập điểm hiện tại và mục tiêu GPA để biết điểm cần đạt cho phần còn lại.")
        sub.setStyleSheet("color:#94A3B8; font-size:12px;")
        sub.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(sub)

        # Scroll chứa nội dung
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(14)

        # Card: Mục tiêu & thang điểm
        top_card = self._make_card()
        tl = QGridLayout(top_card)
        tl.setContentsMargins(18, 16, 18, 16)
        tl.setHorizontalSpacing(14)
        tl.setVerticalSpacing(10)

        tl.addWidget(self._lbl("Mục tiêu GPA:"), 0, 0)
        self.target_gpa = QDoubleSpinBox()
        self.target_gpa.setRange(0.0, 10.0)
        self.target_gpa.setDecimals(2)
        self.target_gpa.setSingleStep(0.1)
        self.target_gpa.setValue(3.5)
        tl.addWidget(self.target_gpa, 0, 1)

        tl.addWidget(self._lbl("Thang điểm:"), 0, 2)
        self.scale = QComboBox()
        self.scale.addItem("Hệ 10", 10.0)
        self.scale.addItem("Hệ 4", 4.0)
        self.scale.currentIndexChanged.connect(self._on_scale_change)
        tl.addWidget(self.scale, 0, 3)

        tl.addWidget(self._lbl("Tỷ trọng còn lại (%):"), 1, 0)
        self.remaining = QDoubleSpinBox()
        self.remaining.setRange(0.0, 100.0)
        self.remaining.setDecimals(1)
        self.remaining.setValue(30.0)
        tl.addWidget(self.remaining, 1, 1)
        tl.setColumnStretch(1, 1)
        tl.setColumnStretch(3, 1)
        body_lay.addWidget(top_card)

        # Card: Bảng điểm hiện tại
        score_card = self._make_card()
        sl = QVBoxLayout(score_card)
        sl.setContentsMargins(18, 16, 18, 16)
        sl.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(self._lbl_bold("Điểm thành phần hiện có"))
        head.addStretch()
        btn_add = QPushButton("➕ Thêm dòng")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._add_score_row)
        head.addWidget(btn_add)
        sl.addLayout(head)

        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(8)
        sl.addLayout(self.rows_container)
        body_lay.addWidget(score_card)

        # Card: Kết quả
        self.result_card = QFrame()
        self.result_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1E1B4B, stop:1 #4C1D95);
                border: 1px solid #7C3AED; border-radius:14px;
            }
        """)
        rl = QVBoxLayout(self.result_card)
        rl.setContentsMargins(22, 18, 22, 18)
        rl.setSpacing(6)
        rl.addWidget(self._lbl("Kết quả ước lượng", color="#C4B5FD", bold=True))
        self.result_label = QLabel("Nhập thông tin và bấm Tính toán")
        self.result_label.setStyleSheet("color:#F8FAFC; font-size:20px; font-weight:bold;")
        self.result_label.setWordWrap(True)
        rl.addWidget(self.result_label)
        self.result_hint = QLabel("")
        self.result_hint.setStyleSheet("color:#C4B5FD; font-size:12px;")
        rl.addWidget(self.result_hint)
        body_lay.addWidget(self.result_card)

        # Nút tính
        actions = QHBoxLayout()
        actions.addStretch()
        self.btn_calc = QPushButton("🧮 Tính điểm cần đạt")
        self.btn_calc.setObjectName("primaryBtn")
        self.btn_calc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_calc.setMinimumHeight(42)
        self.btn_calc.setMinimumWidth(220)
        self.btn_calc.clicked.connect(self._calculate)
        actions.addWidget(self.btn_calc)
        body_lay.addLayout(actions)

        body_lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self.setStyleSheet(self.styleSheet() + """
            QPushButton#primaryBtn {
                background-color:#6D3CCB; border:1px solid #8055D9;
                border-radius:10px; padding:8px 20px; color:white;
                font-weight:bold; font-size:14px;
            }
            QPushButton#primaryBtn:hover { background-color:#7C4FE0; }
            QPushButton#primaryBtn:disabled { background-color:#3F3F66; }
            QDoubleSpinBox, QLineEdit {
                background-color:#0F172A; border:1px solid #2E3B57;
                border-radius:6px; padding:6px 8px; color:#E2E8F0;
            }
            QComboBox {
                background-color:#0F172A; border:1px solid #2E3B57;
                border-radius:6px; padding:6px 8px; color:#E2E8F0;
            }
            QPushButton { /* nút ➕ Thêm dòng */
                background-color:#1A243D; border:1px solid #2E3B57;
                border-radius:8px; padding:5px 12px; color:#CBD5E1;
            }
            QPushButton:hover { background-color:#232F4D; }
        """)

        # Khởi tạo 2 dòng mẫu
        self._add_score_row()
        self._add_score_row()
        self._on_scale_change()

    # ---------- helpers ----------
    def _make_card(self) -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            "background-color:#171D2E; border:1px solid #28334B; border-radius:14px;")
        return f

    def _lbl(self, text: str, color: str = "#CBD5E1", bold: bool = False) -> QLabel:
        lb = QLabel(text)
        weight = "bold" if bold else "normal"
        lb.setStyleSheet(f"color:{color}; font-weight:{weight}; border:none;")
        return lb

    def _lbl_bold(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setStyleSheet(
            "color:#F8FAFC; font-size:14px; font-weight:bold; border:none;")
        return lb

    def _on_scale_change(self):
        scale = float(self.scale.currentData())
        self.target_gpa.setRange(0.0, scale)
        if self.target_gpa.value() > scale:
            self.target_gpa.setValue(scale)

    def _add_score_row(self):
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        score_input = QLineEdit()
        score_input.setPlaceholderText("Điểm (VD: 8.5)")
        score_input.setFixedWidth(120)

        weight_input = QLineEdit()
        weight_input.setPlaceholderText("Tỷ trọng % (VD: 30)")
        weight_input.setFixedWidth(140)

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(32, 32)
        btn_del.setStyleSheet(
            "QPushButton{background:#3B1F2B;border:1px solid #7F1D1D;"
            "border-radius:6px;color:#FCA5A5;font-weight:bold;}"
            "QPushButton:hover{background:#7F1D1D;}"
        )
        btn_del.clicked.connect(lambda _, w=row: self._remove_score_row(w))

        rl.addWidget(self._lbl("Điểm:"))
        rl.addWidget(score_input)
        rl.addSpacing(10)
        rl.addWidget(self._lbl("Tỷ trọng:"))
        rl.addWidget(weight_input)
        rl.addStretch()
        rl.addWidget(btn_del)

        self.rows_container.addWidget(row)
        self._score_rows.append({
            "widget": row, "score": score_input, "weight": weight_input
        })

    def _remove_score_row(self, widget: QWidget):
        self._score_rows = [r for r in self._score_rows if r["widget"] is not widget]
        widget.setParent(None)
        widget.deleteLater()

    # ---------- tính toán ----------
    def _calculate(self):
        current_scores = []
        for r in self._score_rows:
            s_txt = r["score"].text().strip()
            w_txt = r["weight"].text().strip()
            if not s_txt or not w_txt:
                continue
            try:
                s = float(s_txt)
                w = float(w_txt)
            except ValueError:
                QMessageBox.warning(
                    self, "Dữ liệu không hợp lệ",
                    "Điểm và tỷ trọng phải là số thực.")
                return
            if w <= 0:
                QMessageBox.warning(self, "Dữ liệu không hợp lệ",
                                    "Tỷ trọng phải lớn hơn 0.")
                return
            current_scores.append({"score": s, "weightPercent": w})

        sum_weight = sum(x["weightPercent"] for x in current_scores)
        remaining = float(self.remaining.value())

        if sum_weight + remaining > 100.01:
            QMessageBox.warning(
                self, "Không hợp lệ",
                f"Tổng tỷ trọng ({sum_weight + remaining:.1f}%) vượt quá 100%.")
            return

        if not current_scores and remaining <= 0:
            QMessageBox.warning(self, "Không hợp lệ",
                                "Cần ít nhất 1 đầu điểm hoặc tỷ trọng còn lại > 0.")
            return

        target = float(self.target_gpa.value())
        scale  = float(self.scale.currentData())

        payload = ClientPayloadBuilder.build_score_estimate_gpa_payload(
            req_id=ClientPayloadBuilder.next_request_id(),
            current_scores=current_scores,
            remaining_weight_percent=remaining,
            target_gpa=target,
            scale=scale,
        )
        self.btn_calc.setEnabled(False)
        self.btn_calc.setText("⏳ Đang tính...")
        self.api.send(
            payload=payload, token=self.token,
            on_response=self._on_gpa_response,
            on_error=self._on_gpa_error,
        )

    def _on_gpa_response(self, resp: dict):
        self.btn_calc.setEnabled(True)
        self.btn_calc.setText("🧮 Tính điểm cần đạt")

        if not resp.get("success"):
            code = resp.get("errorCode", "")
            msg = resp.get("message", "Không thể tính toán.")
            if code == "SCORE_TARGET_UNACHIEVABLE":
                self.result_label.setText("⚠️ Mục tiêu không khả thi")
                self.result_label.setStyleSheet(
                    "color:#FCA5A5; font-size:18px; font-weight:bold;")
                self.result_hint.setText(
                    "Bạn cần điều chỉnh mục tiêu GPA hoặc nhập thêm điểm đã có.")
            else:
                QMessageBox.warning(self, "Lỗi", msg)
            return

        required = float(resp.get("data", {}).get(
            "requiredScoreForRemainingWeight", 0))
        scale = float(self.scale.currentData())

        if required > scale or required < 0:
            self.result_label.setText("⚠️ Mục tiêu không khả thi")
            self.result_label.setStyleSheet(
                "color:#FCA5A5; font-size:18px; font-weight:bold;")
            self.result_hint.setText(
                f"Điểm cần đạt ({required:.2f}) vượt quá thang điểm {scale:.0f}.")
            return

        self.result_label.setText(f"🎯 Cần đạt: {required:.2f} / {scale:.0f}")
        self.result_label.setStyleSheet(
            "color:#F8FAFC; font-size:22px; font-weight:bold;")
        self.result_hint.setText(
            f"cho {self.remaining.value():.1f}% tỷ trọng còn lại "
            f"để đạt GPA mục tiêu {self.target_gpa.value():.2f}")

    def _on_gpa_error(self, msg: str):
        self.btn_calc.setEnabled(True)
        self.btn_calc.setText("🧮 Tính điểm cần đạt")
        QMessageBox.warning(self, "Lỗi kết nối", msg)


# ============================================================
# WINDOW CHÍNH: GỘP 2 TAB
# ============================================================
class StatisticsWindow(QWidget):
    """
    UC16 + UC18 trong cùng 1 màn hình với tab switcher.
    Class name giữ nguyên để ui_main.py không cần sửa.
    """

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Tab bar
        tab_bar = QFrame()
        tab_bar.setFixedHeight(56)
        tab_bar.setStyleSheet(
            "background-color:#11182C; border-bottom:1px solid #222E47;")
        tbl = QHBoxLayout(tab_bar)
        tbl.setContentsMargins(24, 0, 24, 0)
        tbl.setSpacing(4)

        self.btn_stat = QPushButton("📊  Thống kê trực quan")
        self.btn_gpa  = QPushButton("🎯  Ước lượng GPA")
        for b in (self.btn_stat, self.btn_gpa):
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setMinimumHeight(40)
            tbl.addWidget(b)
        tbl.addStretch()
        self.btn_stat.setChecked(True)

        self.btn_stat.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_gpa.clicked