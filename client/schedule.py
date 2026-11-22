import random
from datetime import datetime, timedelta, timezone
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QDateTimeEdit, QMessageBox
)
from PySide6.QtCore import QDate
from api_worker import APIWorker
from api_client import ClientPayloadBuilder


VIEW_MODES = ["DAY", "WEEK", "MONTH"]
VIEW_LABELS = {"DAY": "Ngày", "WEEK": "Tuần", "MONTH": "Tháng"}
EVENT_TYPES = ["STUDY", "EXAM", "DEADLINE"]
EVENT_LABELS = {"STUDY": "Học tập", "EXAM": "Lịch thi", "DEADLINE": "Deadline"}


def _to_iso_utc(qdt: QDateTime) -> str:
    dt = qdt.toPython()
    if dt.tzinfo is None:
        dt = dt.astimezone()
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso_display(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        cleaned = str(iso_str).replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(iso_str)


def _parse_qdatetime(iso_str: str) -> QDateTime:
    try:
        cleaned = str(iso_str).replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    except ValueError:
        return QDateTime.currentDateTime()


class EventFormDialog(QDialog):
    """Hộp thoại thêm (UC5) hoặc sửa (UC6) sự kiện lịch."""

    def __init__(self, event_data: dict | None = None, parent=None):
        super().__init__(parent)
        self.is_edit = event_data is not None
        self.setWindowTitle("Sửa sự kiện lịch" if self.is_edit else "Thêm sự kiện lịch")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("VD: Ôn tập Cấu trúc rời rạc")

        self.type_combo = QComboBox()
        for et in EVENT_TYPES:
            self.type_combo.addItem(EVENT_LABELS[et], et)

        now = QDateTime.currentDateTime()
        self.start_dt = QDateTimeEdit(now)
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setDisplayFormat("dd/MM/yyyy HH:mm")

        self.end_dt = QDateTimeEdit(now.addSecs(3600))
        self.end_dt.setCalendarPopup(True)
        self.end_dt.setDisplayFormat("dd/MM/yyyy HH:mm")

        if self.is_edit and isinstance(event_data, dict):
            self.title_input.setText(str(event_data.get("title") or ""))
            etype = str(event_data.get("eventType") or "STUDY").upper()
            idx = self.type_combo.findData(etype)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            if event_data.get("startTime"):
                self.start_dt.setDateTime(_parse_qdatetime(event_data["startTime"]))
            if event_data.get("endTime"):
                self.end_dt.setDateTime(_parse_qdatetime(event_data["endTime"]))

        form.addRow("Tiêu đề:", self.title_input)
        form.addRow("Loại sự kiện:", self.type_combo)
        form.addRow("Bắt đầu:", self.start_dt)
        form.addRow("Kết thúc:", self.end_dt)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Hủy", clicked=self.reject)
        save_btn = QPushButton("Lưu sự kiện", objectName="primaryButton", clicked=self._validate_and_accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tiêu đề sự kiện.")
            return
        if self.end_dt.dateTime() <= self.start_dt.dateTime():
            QMessageBox.warning(self, "Thời gian không hợp lệ", "Thời gian kết thúc phải sau thời gian bắt đầu.")
            return
        self.accept()

    def get_form_data(self) -> dict:
        return {
            "title": self.title_input.text().strip(),
            "eventType": self.type_combo.currentData(),
            "startTime": _to_iso_utc(self.start_dt.dateTime()),
            "endTime": _to_iso_utc(self.end_dt.dateTime()),
        }


class ScheduleWindow(QWidget):
    """UC4: Xem thời gian biểu | UC5: Thêm sự kiện | UC6: Sửa sự kiện."""

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.workers: list[APIWorker] = []
        self.events_cache: list[dict] = []

        self._build_ui()
        self._apply_styles()
        self.load_schedule()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Tiêu đề và nút thêm sự kiện
        header = QHBoxLayout()
        header.addWidget(QLabel("Lịch & Thời gian biểu", objectName="pageTitle"))
        header.addStretch()
        self.add_btn = QPushButton(
            "+ Thêm sự kiện", objectName="primaryButton",
            clicked=self.open_add_dialog
        )
        header.addWidget(self.add_btn)
        root.addLayout(header)

        # Thanh điều hướng lịch
        filter_card = QFrame(objectName="card")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(18, 14, 18, 14)
        filter_layout.setSpacing(12)

        filter_layout.addWidget(QLabel("Chế độ xem:"))
        self.view_combo = QComboBox()
        for mode in VIEW_MODES:
            self.view_combo.addItem(VIEW_LABELS[mode], mode)
        self.view_combo.setCurrentIndex(1)  # Mặc định xem theo tuần
        self.view_combo.currentIndexChanged.connect(lambda _: self.load_schedule())
        filter_layout.addWidget(self.view_combo)

        self.prev_btn = QPushButton("‹", clicked=self.go_previous)
        self.prev_btn.setFixedWidth(36)
        filter_layout.addWidget(self.prev_btn)

        self.anchor_date = QDateEdit(QDate.currentDate())
        self.anchor_date.setCalendarPopup(True)
        self.anchor_date.setDisplayFormat("dd/MM/yyyy")
        self.anchor_date.dateChanged.connect(lambda _: self.load_schedule())
        self.anchor_date.setFixedWidth(130)
        filter_layout.addWidget(self.anchor_date)

        self.next_btn = QPushButton("›", clicked=self.go_next)
        self.next_btn.setFixedWidth(36)
        filter_layout.addWidget(self.next_btn)

        today_btn = QPushButton("Hôm nay", clicked=self.go_today)
        filter_layout.addWidget(today_btn)

        refresh_btn = QPushButton("Tải lại", clicked=self.load_schedule)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addStretch()

        self.range_label = QLabel("", objectName="mutedText")
        filter_layout.addWidget(self.range_label)
        root.addWidget(filter_card)

        # Lịch dạng ô: 1 cột (Ngày), 7 cột (Tuần), 7x6 ô (Tháng)
        calendar_card = QFrame(objectName="card")
        calendar_layout = QVBoxLayout(calendar_card)
        calendar_layout.setContentsMargins(14, 14, 14, 14)
        calendar_layout.setSpacing(8)

        self.day_headers = QTableWidget(0, 7, objectName="day_headers")
        self.day_headers.setHorizontalHeaderLabels(
            ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
        )
        self.day_headers.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.day_headers.verticalHeader().setVisible(False)
        self.day_headers.setFixedHeight(38)
        self.day_headers.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.day_headers.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        calendar_layout.addWidget(self.day_headers)

        self.calendar = QTableWidget(1, 7, objectName="calendar")
        self.calendar.horizontalHeader().setVisible(False)
        self.calendar.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.calendar.verticalHeader().setVisible(False)
        self.calendar.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.calendar.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.calendar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.calendar.setShowGrid(True)
        calendar_layout.addWidget(self.calendar, stretch=1)

        self.status_label = QLabel("Đang tải lịch...", objectName="mutedText")
        calendar_layout.addWidget(self.status_label)
        root.addWidget(calendar_card, stretch=1)

    def _get_date_range(self) -> tuple[str, str, str]:
        mode = self.view_combo.currentData() or "WEEK"
        qd = self.anchor_date.date()
        py_date = datetime(qd.year(), qd.month(), qd.day())

        if mode == "DAY":
            start_dt = py_date
            end_dt = py_date
            label = f"Ngày {qd.toString('dd/MM/yyyy')}"
        elif mode == "MONTH":
            first_day = QDate(qd.year(), qd.month(), 1)
            first_cell = first_day.addDays(-(first_day.dayOfWeek() - 1))
            last_day = first_day.addMonths(1).addDays(-1)
            last_cell = last_day.addDays(7 - last_day.dayOfWeek())
            start_dt = datetime(first_cell.year(), first_cell.month(), first_cell.day())
            end_dt = datetime(last_cell.year(), last_cell.month(), last_cell.day())
            label = f"Tháng {qd.month():02d}/{qd.year()}"
        else:  # WEEK (Thứ 2 -> Chủ nhật)
            monday = py_date - timedelta(days=py_date.weekday())
            sunday = monday + timedelta(days=6)
            start_dt = monday
            end_dt = sunday
            label = f"Tuần {monday.strftime('%d/%m')} - {sunday.strftime('%d/%m/%Y')}"

        return (
            start_dt.strftime("%Y-%m-%d"),
            end_dt.strftime("%Y-%m-%d"),
            label,
        )

    def go_previous(self):
        mode = self.view_combo.currentData()
        date = self.anchor_date.date()
        if mode == "DAY":
            date = date.addDays(-1)
        elif mode == "WEEK":
            date = date.addDays(-7)
        else:
            date = date.addMonths(-1)
        self.anchor_date.setDate(date)

    def go_next(self):
        mode = self.view_combo.currentData()
        date = self.anchor_date.date()
        if mode == "DAY":
            date = date.addDays(1)
        elif mode == "WEEK":
            date = date.addDays(7)
        else:
            date = date.addMonths(1)
        self.anchor_date.setDate(date)

    def go_today(self):
        self.anchor_date.setDate(QDate.currentDate())

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
                msg = res.get("message") or "Máy chủ không xử lý được yêu cầu."
                QMessageBox.warning(self, "Thông báo", msg)
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

    # === UC4: XEM THỜI GIAN BIỂU ===
    def load_schedule(self):
        mode = self.view_combo.currentData() or "WEEK"
        start_date, end_date, range_text = self._get_date_range() #Nhận chuỗi ngày YYYY-MM-DD
        self.range_label.setText(range_text)
        self.status_label.setText("Đang tải danh sách sự kiện...")

        local_tz = datetime.now().astimezone().tzname() or "UTC"

        def on_loaded(res: dict):
            data = res.get("data") or {}
            events = data.get("events") or []
            self.events_cache = [e for e in events if isinstance(e, dict)]
            self._render_calendar()
            self.status_label.setText(
                f"Hiển thị {len(self.events_cache)} sự kiện ({VIEW_LABELS.get(mode, mode)})."
            )

        self._send_api(
            "/api/schedule/list",
            "SCHEDULE_GET_LIST",
            {
                "viewMode": mode,
                "startDate": start_date,
                "endDate": end_date,
                "timezone": local_tz,
            },
            on_loaded,
            lambda _: self.status_label.setText("Không tải được lịch biểu."),
        )

    def _render_calendar(self):
        """Vẽ sự kiện vào các ô ngày tương ứng trong lịch Ngày/Tuần/Tháng."""
        mode = self.view_combo.currentData() or "WEEK"
        anchor = self.anchor_date.date()

        # Xác định các ngày sẽ hiển thị trên lịch.
        if mode == "DAY":
            visible_dates = [anchor]
            row_count, col_count = 1, 1
            self.day_headers.setVisible(False)
        elif mode == "WEEK":
            monday = anchor.addDays(-(anchor.dayOfWeek() - 1))
            visible_dates = [monday.addDays(i) for i in range(7)]
            row_count, col_count = 1, 7
            self.day_headers.setVisible(True)
        else:
            first_day = QDate(anchor.year(), anchor.month(), 1)
            # Lịch tháng bắt đầu từ thứ Hai; luôn hiển thị đủ 6 hàng.
            first_cell = first_day.addDays(-(first_day.dayOfWeek() - 1))
            visible_dates = [first_cell.addDays(i) for i in range(42)]
            row_count, col_count = 6, 7
            self.day_headers.setVisible(True)

        self.calendar.clearContents()
        self.calendar.setRowCount(row_count)
        self.calendar.setColumnCount(col_count)
        if mode == "DAY":
            self.calendar.setColumnWidth(0, self.calendar.viewport().width())
            self.calendar.setRowHeight(0, max(380, self.calendar.viewport().height()))
        elif mode == "WEEK":
            self.calendar.setRowHeight(0, max(420, self.calendar.viewport().height()))
        else:
            for row in range(6):
                self.calendar.setRowHeight(row, 125)

        # Gom sự kiện theo ngày bắt đầu. Thời gian hiển thị được đổi về múi giờ máy.
        events_by_date = {}
        for event in self.events_cache:
            raw_start = event.get("startTime") or ""
            try:
                dt = datetime.fromisoformat(str(raw_start).replace("Z", "+00:00"))
                if dt.tzinfo is not None:
                    dt = dt.astimezone()
                event_date = QDate(dt.year, dt.month, dt.day)
                events_by_date.setdefault(event_date.toString("yyyy-MM-dd"), []).append(event)
            except ValueError:
                continue

        for index, qdate in enumerate(visible_dates):
            row = index // col_count
            col = index % col_count
            cell = QWidget()
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(6, 5, 6, 5)
            cell_layout.setSpacing(4)

            date_label = QLabel(str(qdate.day()))
            date_label.setObjectName("calendarDate")
            if qdate == QDate.currentDate():
                date_label.setStyleSheet(
                    "background-color: #6D3CCB; color: white; border-radius: 10px; "
                    "padding: 3px 8px; font-weight: bold;"
                )
            elif mode == "MONTH" and qdate.month() != anchor.month():
                date_label.setStyleSheet("color: #64748B; padding: 3px;")
            else:
                date_label.setStyleSheet("color: #E2E8F0; padding: 3px; font-weight: bold;")
            cell_layout.addWidget(date_label, alignment=Qt.AlignmentFlag.AlignLeft)

            key = qdate.toString("yyyy-MM-dd")
            day_events = events_by_date.get(key, [])
            for event in day_events:
                event_type = str(event.get("eventType") or "STUDY").upper()
                title = str(event.get("title") or "Sự kiện")
                start_text = _parse_iso_display(event.get("startTime", ""))
                time_text = start_text[-5:] if len(start_text) >= 5 else ""

                event_card = QFrame()
                event_card.setObjectName("calendarEvent")
                event_layout = QVBoxLayout(event_card)
                event_layout.setContentsMargins(6, 4, 6, 4)
                event_layout.setSpacing(2)

                type_label = QLabel(EVENT_LABELS.get(event_type, event_type))
                type_label.setObjectName("calendarEventType")
                title_btn = QPushButton(title)
                title_btn.setObjectName("calendarEventTitle")
                title_btn.setToolTip(f"{title}\nNhấn để chỉnh sửa")
                title_btn.setStyleSheet(
                    "text-align: left; padding: 2px; border: none; "
                    "background: transparent; color: #F8FAFC;"
                )
                title_btn.clicked.connect(
                    lambda checked=False, item=event: self.open_edit_dialog(item)
                )
                time_label = QLabel(time_text)
                time_label.setObjectName("calendarEventTime")

                event_layout.addWidget(type_label)
                event_layout.addWidget(title_btn)
                event_layout.addWidget(time_label)

                actions = QHBoxLayout()
                actions.setContentsMargins(0, 0, 0, 0)
                edit_btn = QPushButton("Sửa")
                edit_btn.setObjectName("smallActionButton")
                edit_btn.clicked.connect(
                    lambda checked=False, item=event: self.open_edit_dialog(item)
                )
                delete_btn = QPushButton("Xóa")
                delete_btn.setObjectName("smallDeleteButton")
                delete_btn.clicked.connect(
                    lambda checked=False, item=event: self.delete_event(item)
                )
                actions.addWidget(edit_btn)
                actions.addWidget(delete_btn)
                actions.addStretch()
                event_layout.addLayout(actions)
                cell_layout.addWidget(event_card)

            if not day_events:
                empty_label = QLabel("Không có sự kiện")
                empty_label.setObjectName("calendarEmpty")
                cell_layout.addWidget(empty_label)

            cell_layout.addStretch()
            self.calendar.setCellWidget(row, col, cell)

        self.calendar.resizeRowsToContents()
        if mode == "MONTH":
            for row in range(6):
                self.calendar.setRowHeight(row, max(125, self.calendar.rowHeight(row)))
        elif mode == "WEEK":
            self.calendar.setRowHeight(0, max(420, self.calendar.rowHeight(0)))
        else:
            self.calendar.setRowHeight(0, max(380, self.calendar.rowHeight(0)))

    # === UC5: THÊM SỰ KIỆN LỊCH ===
    def open_add_dialog(self):
        dlg = EventFormDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        form_data = dlg.get_form_data()
        self.add_btn.setEnabled(False)

        def on_added(res: dict):
            self.add_btn.setEnabled(True)
            QMessageBox.information(self, "Thành công", res.get("message") or "Đã thêm sự kiện lịch.")
            self.load_schedule()

        self._send_api(
            "/api/schedule/add",
            "SCHEDULE_ADD",
            form_data,
            on_added,
            lambda _: self.add_btn.setEnabled(True),
        )

    # === UC6: SỬA SỰ KIỆN LỊCH ===
    def open_edit_dialog(self, event_data: dict):
        event_id = event_data.get("eventId")
        if event_id is None:
            QMessageBox.warning(self, "Lỗi dữ liệu", "Sự kiện thiếu eventId.")
            return

        dlg = EventFormDialog(event_data=event_data, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        payload_data = {"eventId": event_id, **dlg.get_form_data()}

        def on_updated(res: dict):
            QMessageBox.information(self, "Thành công", res.get("message") or "Đã cập nhật sự kiện.")
            self.load_schedule()

        self._send_api(
            "/api/schedule/update",
            "SCHEDULE_UPDATE",
            payload_data,
            on_updated,
        )

    # === UC7: XÓA SỰ KIỆN LỊCH ===
    def delete_event(self, event_data: dict):
        event_id = event_data.get("eventId")  # Lấy ID sự kiện cần xóa
        if event_id is None:
            QMessageBox.warning(self, "Lỗi dữ liệu", "Sự kiện thiếu eventId.")
            return

        title = str(event_data.get("title") or "sự kiện này")
        confirm = QMessageBox.question(  # Hỏi xác nhận trước khi xóa
            self,
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa '{title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        def on_deleted(res: dict):
            QMessageBox.information(self, "Thành công", res.get("message") or "Đã xóa sự kiện.")
            self.load_schedule()  # Tải lại danh sách sự kiện sau khi xóa

        self._send_api(
            "/api/schedule/delete",
            "SCHEDULE_DELETE",
            {"eventId": event_id},
            on_deleted,
        )

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #0B1020; color: #F1F5F9; font-size: 14px; }
            QLabel { background: transparent; }
            QLabel#pageTitle { color: #F8FAFC; font-size: 24px; font-weight: bold; }
            QLabel#mutedText { color: #94A3B8; font-size: 12px; }
            QFrame#card { background-color: #171D2E; border: 1px solid #28334B; border-radius: 14px; }
            QComboBox, QDateEdit, QDateTimeEdit, QLineEdit {
                background-color: #0F172A; color: #F8FAFC;
                border: 1px solid #35415A; border-radius: 7px; padding: 7px 10px;
            }
            QTableWidget {
                background-color: #0F172A; color: #F1F5F9;
                border: 1px solid #28334B; border-radius: 8px; gridline-color: #1E293B;
            }
            QHeaderView::section {
                background-color: #1E293B; color: #E2E8F0;
                padding: 8px; border: none; font-weight: bold;
            }
            QPushButton {
                background-color: #263248; color: #E2E8F0;
                border: 1px solid #35415A; border-radius: 8px; padding: 7px 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #35435D; }
            QPushButton#primaryButton { background-color: #6D3CCB; border: 1px solid #8055D9; color: #FFFFFF; }
            QPushButton#primaryButton:hover { background-color: #8055D9; }
            QTableWidget#calendar { background-color: #0F172A; gridline-color: #28334B; }
            QTableWidget#calendar::item { border: 1px solid #28334B; }
            QTableWidget#day_headers { background-color: #1E293B; }
            QFrame#calendarEvent {
                background-color: #263248; border: 1px solid #40506D; border-radius: 6px;
            }
            QLabel#calendarEventType { color: #A5B4FC; font-size: 10px; font-weight: bold; }
            QLabel#calendarEventTime { color: #CBD5E1; font-size: 10px; }
            QLabel#calendarEmpty { color: #64748B; font-size: 10px; }
            QPushButton#calendarEventTitle { font-size: 11px; font-weight: bold; }
            QPushButton#smallActionButton, QPushButton#smallDeleteButton {
                font-size: 10px; padding: 2px 6px; border-radius: 4px;
            }
            QPushButton#smallDeleteButton { color: #FCA5A5; }
        """)