import random
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QListWidget, QListWidgetItem, QCheckBox, QLineEdit, QTextEdit,
    QDialog, QFormLayout, QSpinBox, QMessageBox
)
from api_worker import APIWorker
from api_client import ClientPayloadBuilder


class NoteFormDialog(QDialog):
    """Hộp thoại thêm (UC9) hoặc sửa (UC10) ghi chú / to-do item."""

    def __init__(self, note_data: dict | None = None, parent=None):
        super().__init__(parent)
        self.is_edit = note_data is not None
        self.setWindowTitle("Sửa ghi chú" if self.is_edit else "Thêm ghi chú mới")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Tiêu đề ghi chú hoặc công việc")

        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(120)
        self.content_input.setPlaceholderText("Nhập nội dung...")

        self.todo_check = QCheckBox("Đánh dấu là To-do list")
        self.done_check = QCheckBox("Đã hoàn thành")

        if self.is_edit and isinstance(note_data, dict):
            self.title_input.setText(str(note_data.get("title") or ""))
            self.content_input.setPlainText(str(note_data.get("content") or ""))
            self.todo_check.setChecked(bool(note_data.get("isTodoList", False)))
            self.done_check.setChecked(bool(note_data.get("isDone", False)))

        form.addRow("Tiêu đề:", self.title_input)
        form.addRow("Nội dung:", self.content_input)
        form.addRow("", self.todo_check)
        if self.is_edit:
            form.addRow("Trạng thái:", self.done_check)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Hủy", clicked=self.reject)
        save_btn = QPushButton("Lưu", objectName="primaryButton", clicked=self._validate_and_accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        content = self.content_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Nội dung rỗng", "Vui lòng nhập nội dung ghi chú.")
            return
        self.accept()

    def get_form_data(self) -> dict:
        data = {
            "title": self.title_input.text().strip() or "Ghi chú không tiêu đề",
            "content": self.content_input.toPlainText().strip(),
            "isTodoList": self.todo_check.isChecked(),
        }
        if self.is_edit:
            data["isDone"] = self.done_check.isChecked()
        return data


class NotesWindow(QWidget):
    """UC8: Xem danh sách ghi chú | UC9: Thêm ghi chú | UC10: Sửa ghi chú."""

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.workers: list[APIWorker] = []
        self.current_page = 1
        self.total_pages = 1
        self.limit = 10
        self.notes_cache: list[dict] = []

        self._build_ui()
        self._apply_styles()
        self.load_notes()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(QLabel("Ghi chú & To-do list", objectName="pageTitle"))
        header.addStretch()
        self.add_btn = QPushButton("+ Thêm ghi chú", objectName="primaryButton", clicked=self.open_add_dialog)
        header.addWidget(self.add_btn)
        root.addLayout(header)

        # Thanh phân trang & lọc nhanh
        bar = QFrame(objectName="card")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(18, 12, 18, 12)
        bar_layout.setSpacing(10)

        self.only_todo_check = QCheckBox("Chỉ hiện To-do list")
        self.only_todo_check.stateChanged.connect(lambda _: self._render_list())
        bar_layout.addWidget(self.only_todo_check)

        bar_layout.addStretch()
        bar_layout.addWidget(QLabel("Số mục/trang:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(5, 50)
        self.limit_spin.setValue(self.limit)
        self.limit_spin.valueChanged.connect(self._on_limit_changed)
        bar_layout.addWidget(self.limit_spin)

        self.prev_btn = QPushButton("◀ Trước", clicked=self._prev_page)
        self.page_info_label = QLabel("Trang 1/1", objectName="mutedText")
        self.next_btn = QPushButton("Sau ▶", clicked=self._next_page)
        bar_layout.addWidget(self.prev_btn)
        bar_layout.addWidget(self.page_info_label)
        bar_layout.addWidget(self.next_btn)
        root.addWidget(bar)

        # Danh sách ghi chú / to-do
        list_card = QFrame(objectName="card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(18, 16, 18, 16)
        list_layout.setSpacing(10)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(8)
        list_layout.addWidget(self.list_widget)

        self.status_label = QLabel("Đang tải ghi chú...", objectName="mutedText")
        list_layout.addWidget(self.status_label)
        root.addWidget(list_card, stretch=1)

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

    def _on_limit_changed(self, val: int):
        self.limit = val
        self.current_page = 1
        self.load_notes()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_notes()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_notes()

    # === UC8: XEM DANH SÁCH GHI CHÚ ===
    def load_notes(self):
        self.status_label.setText("Đang tải danh sách ghi chú...")

        def on_loaded(res: dict):
            data = res.get("data") or {}
            notes = data.get("notes") or []
            self.notes_cache = [n for n in notes if isinstance(n, dict) and not n.get("isDeleted", False)]
            self.total_pages = max(1, int(data.get("totalPages") or 1))
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages

            self.page_info_label.setText(f"Trang {self.current_page}/{self.total_pages}")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)

            self._render_list()
            total_count = data.get("totalCount", len(self.notes_cache))
            self.status_label.setText(f"Tổng cộng: {total_count} mục.")

        self._send_api(
            "/api/note/list",
            "NOTE_GET_LIST",
            {"page": self.current_page, "limit": self.limit},
            on_loaded,
            lambda _: self.status_label.setText("Không tải được danh sách ghi chú."),
        )

    def _render_list(self):
        self.list_widget.clear()
        only_todo = self.only_todo_check.isChecked()

        for note in self.notes_cache:
            is_todo = bool(note.get("isTodoList", False))
            if only_todo and not is_todo:
                continue

            item = QListWidgetItem(self.list_widget)
            row_widget = QFrame(objectName="noteRow")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(14, 10, 14, 10)
            row_layout.setSpacing(12)

            if is_todo:
                done_box = QCheckBox()
                done_box.setChecked(bool(note.get("isDone", False)))
                done_box.stateChanged.connect(lambda state, n=note: self._toggle_done(n, state == Qt.CheckState.Checked.value))
                row_layout.addWidget(done_box)

            text_col = QVBoxLayout()
            text_col.setSpacing(4)
            badge = "[To-do] " if is_todo else "[Ghi chú] "
            title_lbl = QLabel(f"{badge}{note.get('title') or ''}", objectName="noteTitle")
            if is_todo and note.get("isDone"):
                title_lbl.setStyleSheet("text-decoration: line-through; color: #94A3B8;")
            content_lbl = QLabel(str(note.get("content") or ""), objectName="mutedText")
            content_lbl.setWordWrap(True)
            text_col.addWidget(title_lbl)
            text_col.addWidget(content_lbl)
            row_layout.addLayout(text_col, stretch=1)

            edit_btn = QPushButton("Sửa", clicked=lambda _, n=note: self.open_edit_dialog(n))  # Nút sửa ghi chú
            del_btn = QPushButton("Xóa", clicked=lambda _, n=note: self.delete_note(n))  # [MỚI] Nút xóa gọi delete_note
            row_layout.addWidget(edit_btn)
            row_layout.addWidget(del_btn)

            item.setSizeHint(row_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row_widget)

    def _toggle_done(self, note: dict, is_done: bool):
        note_id = note.get("noteId")
        if note_id is None:
            return
        self._send_api(
            "/api/note/update",
            "NOTE_UPDATE",
            {
                "noteId": note_id,
                "title": note.get("title") or "",
                "content": note.get("content") or "",
                "isTodoList": bool(note.get("isTodoList", True)),
                "isDone": is_done,
            },
            lambda _: self.load_notes(),
        )

    # === UC9: THÊM GHI CHÚ ===
    def open_add_dialog(self):
        dlg = NoteFormDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        form_data = dlg.get_form_data()
        self.add_btn.setEnabled(False)

        def on_added(res: dict):
            self.add_btn.setEnabled(True)
            QMessageBox.information(self, "Thành công", res.get("message") or "Đã thêm ghi chú.")
            self.load_notes()

        self._send_api(
            "/api/note/add",
            "NOTE_ADD",
            form_data,
            on_added,
            lambda _: self.add_btn.setEnabled(True),
        )

    # === UC10: SỬA GHI CHÚ ===
    def open_edit_dialog(self, note: dict):
        note_id = note.get("noteId")
        if note_id is None:
            QMessageBox.warning(self, "Lỗi dữ liệu", "Ghi chú thiếu noteId.")
            return

        dlg = NoteFormDialog(note_data=note, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        payload_data = {"noteId": note_id, **dlg.get_form_data()}

        def on_updated(res: dict):
            QMessageBox.information(self, "Thành công", res.get("message") or "Cập nhật thành công.")
            self.load_notes()

        self._send_api(
            "/api/note/update",
            "NOTE_UPDATE",
            payload_data,
            on_updated,
        )

    # === UC11: XÓA GHI CHÚ ===
    def delete_note(self, note: dict): 
        note_id = note.get("noteId")  #Lấy noteId của ghi chú
        if note_id is None: 
            QMessageBox.warning(self, "Lỗi dữ liệu", "Ghi chú thiếu noteId.")  # [MỚI] Thông báo lỗi dữ liệu
            return

        title = str(note.get("title") or "ghi chú này")  # Lấy tiêu đề ghi chú để hiển thị xác nhận
        confirm = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa '{title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes: 
            return

        def on_deleted(res: dict):  # Callback khi xóa thành công
            QMessageBox.information(self, "Thành công", res.get("message") or "Đã xóa ghi chú.")  
            self.load_notes()  # Tải lại note list

        self._send_api(  # Gửi yêu cầu xóa ghi chú lên server
            "/api/note/delete", 
            "NOTE_DELETE",
            {"noteId": note_id},
            on_deleted,  
        )

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #0B1020; color: #F1F5F9; font-size: 14px; }
            QLabel { background: transparent; }
            QLabel#pageTitle { color: #F8FAFC; font-size: 24px; font-weight: bold; }
            QLabel#noteTitle { color: #F8FAFC; font-weight: bold; }
            QLabel#mutedText { color: #94A3B8; font-size: 12px; }
            QFrame#card { background-color: #171D2E; border: 1px solid #28334B; border-radius: 14px; }
            QFrame#noteRow { background-color: #0F172A; border: 1px solid #28334B; border-radius: 10px; }
            QListWidget { background: transparent; border: none; }
            QLineEdit, QTextEdit, QSpinBox {
                background-color: #0F172A; color: #F8FAFC;
                border: 1px solid #35415A; border-radius: 7px; padding: 7px 10px;
            }
            QPushButton {
                background-color: #263248; color: #E2E8F0;
                border: 1px solid #35415A; border-radius: 8px; padding: 7px 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #35435D; }
            QPushButton#primaryButton { background-color: #6D3CCB; border: 1px solid #8055D9; color: #FFFFFF; }
            QPushButton#primaryButton:hover { background-color: #8055D9; }
        """)