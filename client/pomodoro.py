import random
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QSpinBox, QFormLayout, QMessageBox, QInputDialog
from api_worker import APIWorker
from api_client import ClientPayloadBuilder

class PomodoroWindow(QWidget):
    """
    UC1: Chạy / Tạm dừng / Tiếp tục / Dừng Pomodoro
    UC2: Đọc và cập nhật thời gian tập trung, nghỉ
    UC3: Đọc và đồng bộ tùy chọn Mini-player

    Khởi tạo từ màn hình đã đăng nhập:
        self.pomodoro_window = PomodoroWindow(token)
        self.pomodoro_window.show()
    """
    session_stop = Signal(dict)
    mini_player_toggled = Signal(bool)

    def __init__(self, token: str):
        super().__init__()

        self.token = token
        self.session_id = None
        self.focus_minutes = 25
        self.break_minutes = 5
        self.remaining_seconds = self.focus_minutes * 60
        self.current_phase = "FOCUS"   # FOCUS/BREAK
        self.timer_state = "IDLE"      # IDLE/ RUNNING/ PAUSED
        self.is_mini_player = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000) # đồng hộ tự đếm lùi mỗi 1s
        self.timer.timeout.connect(self.update_countdown)

        self.workers = [] # Giữ các APIWorker đang chạy để không bị hủy sớm

        self.setWindowTitle("Study Management - Pomodoro")
        self.resize(760, 620)
        self.setMinimumSize(520, 480)

        self.build_ui() # UC1
        self.load_settings() # UC2
        self.load_mini_player_preference() # UC3

    # === GIAO DIỆN ===
    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 26, 30, 26)
        main_layout.setSpacing(18)

        self.header_widget = QWidget()
        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(0, 0, 0, 0)
        brand = QLabel("◈ StudyManagement", objectName="brandTitle")
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(QLabel("POMODORO TIMER", objectName="headerTag"))
        main_layout.addWidget(self.header_widget)

        # Thẻ đồng hồ
        self.timer_card = QFrame(objectName="timerCard")
        timer_layout = QVBoxLayout(self.timer_card)
        timer_layout.setContentsMargins(26, 24, 26, 24)
        timer_layout.setSpacing(12)

        self.phase_label = QLabel("THỜI GIAN TẬP TRUNG", objectName="phaseLabel")
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label = QLabel("25:00", objectName="timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("Sẵn sàng bắt đầu phiên học", objectName="statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        timer_layout.addWidget(self.phase_label)
        timer_layout.addWidget(self.time_label)
        timer_layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("Bắt đầu", clicked=self.start_session)
        self.pause_button = QPushButton("Tạm dừng", clicked=self.pause_session)
        self.resume_button = QPushButton("Tiếp tục", clicked=self.resume_session)
        self.stop_button = QPushButton("Dừng phiên", clicked=self.stop_session)

        self.start_button.setObjectName("primaryButton")
        self.stop_button.setObjectName("dangerButton")

        buttons.addWidget(self.start_button)
        buttons.addWidget(self.pause_button)
        buttons.addWidget(self.resume_button)
        buttons.addWidget(self.stop_button)
        timer_layout.addLayout(buttons)
        main_layout.addWidget(self.timer_card)

        # Cài đặt thời gian
        self.settings_card = QFrame(objectName="settingsCard")
        settings_layout = QVBoxLayout(self.settings_card)
        settings_layout.setContentsMargins(20, 18, 20, 18)
        settings_layout.setSpacing(12)

        settings_title = QLabel("Cài đặt thời gian", objectName="sectionTitle")
        settings_layout.addWidget(settings_title)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setSuffix(" phút")
        self.focus_spin.setValue(self.focus_minutes)

        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setSuffix(" phút")
        self.break_spin.setValue(self.break_minutes)

        form.addRow("Thời gian tập trung:", self.focus_spin)
        form.addRow("Thời gian nghỉ:", self.break_spin)
        settings_layout.addLayout(form)

        self.save_settings_button = QPushButton( "Lưu", clicked=self.update_settings)
        settings_layout.addWidget(self.save_settings_button, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.settings_card)

        # Mini-player
        bottom = QHBoxLayout()
        self.mini_button = QPushButton("Ghim", clicked=self.toggle_mini_player)
        self.mini_button.setObjectName("secondaryButton")
        bottom.addStretch()
        bottom.addWidget(self.mini_button)
        main_layout.addLayout(bottom)

        self.setStyleSheet("""
            QWidget {background-color: #0B1020; color: #F1F5F9; font-size: 14px;}
            QLabel { background: transparent; }
            QLabel#brandTitle {color: #C4B5FD; font-size: 19px; font-weight: bold;}
            QLabel#headerTag {color: #A78BFA; font-size: 11px; font-weight: bold; letter-spacing: 1px;}
            QLabel#pageTitle {color: #F8FAFC; font-size: 27px; font-weight: bold;}
            QLabel#pageDescription, QLabel#footerNote {color: #94A3B8; font-size: 12px;}
            QFrame#timerCard, QFrame#settingsCard {background-color: #171D2E; border: 1px solid #28334B; border-radius: 15px;}
            QLabel#phaseLabel {color: #A78BFA; font-size: 12px; font-weight: bold;letter-spacing: 1px;}
            QLabel#timeLabel {color: #F8FAFC; font-size: 62px; font-weight: bold;}
            QLabel#statusLabel { color: #94A3B8; font-size: 12px; }
            QLabel#sectionTitle {color: #F8FAFC; font-size: 17px; font-weight: bold;}
            QSpinBox {background-color: #0F172A; color: #F8FAFC; border: 1px solid #35415A; border-radius: 7px; padding: 8px; min-width: 110px;}
            QPushButton {background-color: #263248; color: #E2E8F0; border: 1px solid #35415A; border-radius: 8px; padding: 9px 14px; font-weight: bold;}
            QPushButton:hover { background-color: #35435D; }
            QPushButton:disabled { color: #64748B; background-color: #1E293B;}
            QPushButton#primaryButton { background-color: #6D3CCB; border: 1px solid #8055D9; color: white;}
            QPushButton#primaryButton:hover { background-color: #8055D9; }
            QPushButton#dangerButton {background-color: #7F1D1D; border: 1px solid #991B1B; color: white;}
            QPushButton#secondaryButton {color: #DDD6FE; border: 1px solid #6245A5;}
        """)
        self.refresh_controls()

    # === HÀM DÙNG CHUNG ĐỂ GỌI API ===
    def send_api(self, endpoint: str, action: str, data: dict, on_success, on_error=None): 
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
                QMessageBox.warning(self, "API không thành công", response.get("message") or "Máy chủ không xử lý được yêu cầu.")
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
        worker.start()

    # === UC2: CẬP NHẬT CẤU HÌNH POMODORO ===
    def load_settings(self):
        def on_loaded(res):
            data = res.get("data") or {}
            if isinstance(data.get("focusMinutes"), int) and data["focusMinutes"] > 0:
                self.focus_minutes = data["focusMinutes"]
                self.focus_spin.setValue(self.focus_minutes)
            if isinstance(data.get("breakMinutes"), int) and data["breakMinutes"] > 0:
                self.break_minutes = data["breakMinutes"]
                self.break_spin.setValue(self.break_minutes)
            if self.timer_state == "IDLE" and self.current_phase == "FOCUS":
                self.remaining_seconds = self.focus_minutes * 60
                self.update_time_label()

        self.send_api("/api/pomodoro/settings/get", "POMODORO_SETTINGS_GET", {}, on_loaded)

    def update_settings(self):
        if self.timer_state != "IDLE":
            QMessageBox.information(self, "Thông báo", "Hãy dừng phiên hiện tại trước khi đổi cấu hình.")
            return

        focus, rest = self.focus_spin.value(), self.break_spin.value()
        # Bắt lỗi nhập liệu cục bộ (UC2)
        if focus <= 0 or rest <= 0:
            QMessageBox.warning(self, "Dữ liệu không hợp lệ", "Thời gian tập trung và nghỉ phải lớn hơn 0 phút.")
            return

        self.save_settings_button.setEnabled(False)

        def ok(res):
            self.save_settings_button.setEnabled(True)
            data = res.get("data") or {}
            self.focus_minutes = data.get("focusMinutes", focus)
            self.break_minutes = data.get("breakMinutes", rest)
            self.remaining_seconds = self.focus_minutes * 60
            self.update_time_label()
            QMessageBox.information(self, "Thành công", res.get("message") or "Đã lưu cấu hình.")

        self.send_api(
            "/api/pomodoro/settings/update",
            "POMODORO_SETTINGS_UPDATE",
            {"focusMinutes": focus, "breakMinutes": rest},
            ok,
            lambda _: self.save_settings_button.setEnabled(True)
        )
    
    # === UC1: START / PAUSE / RESUME / STOP ===
    def start_session(self):
        if self.timer_state != "IDLE":
            return

        focus = self.focus_spin.value()
        rest = self.break_spin.value()

        self.start_button.setEnabled(False)
        self.status_label.setText("Đang tạo phiên Pomodoro...")

        def success(response):
            data = response.get("data") or {}
            self.session_id = data.get("sessionId")

            if self.session_id is None:
                self.start_button.setEnabled(True)
                self.status_label.setText("Máy chủ không trả về sessionId.")
                QMessageBox.warning( self, "Lỗi dữ liệu", "Phản hồi POMODORO_START không có sessionId.")
                return

            self.focus_minutes = focus
            self.break_minutes = rest
            self.current_phase = "FOCUS"
            self.remaining_seconds = focus * 60
            self.timer_state = "RUNNING"
            self.timer.start()

            self.status_label.setText( response.get("message") or "Phiên học đang chạy.")
            self.update_time_label()
            self.refresh_controls()

        def error(_response):
            self.start_button.setEnabled(True)
            self.status_label.setText("Không thể bắt đầu phiên học.")

        self.send_api(
            "/api/pomodoro/start",
            "POMODORO_START",
            {
                "planId": None,
                "focusMinutes": focus,
                "breakMinutes": rest
            },
            success,
            error
        )

    def pause_session(self):
        if self.timer_state != "RUNNING" or self.session_id is None:
            return

        self.pause_button.setEnabled(False)

        def success(response):
            self.timer.stop()
            self.timer_state = "PAUSED"
            self.status_label.setText(
                response.get("message") or "Phiên học đã tạm dừng."
            )
            self.refresh_controls()

        def error(_response):
            self.pause_button.setEnabled(True)

        self.send_api(
            "/api/pomodoro/pause",
            "POMODORO_PAUSE",
            {"sessionId": self.session_id},
            success,
            error
        )

    def resume_session(self):
        if self.timer_state != "PAUSED" or self.session_id is None:
            return
        self.resume_button.setEnabled(False)

        def success(response):
            self.timer_state = "RUNNING"
            self.timer.start()
            self.status_label.setText( response.get("message") or "Phiên học đã tiếp tục.")
            self.update_time_label()
            self.refresh_controls()

        def error(_response):
            self.resume_button.setEnabled(True)

        self.send_api(
            "/api/pomodoro/resume",
            "POMODORO_RESUME",
            {"sessionId": self.session_id},
            success,
            error
        )

    def stop_session(self):
        if self.timer_state == "IDLE" or self.session_id is None:
            return

        confirm = QMessageBox.question(
            self,
            "Dừng phiên Pomodoro",
            "Bạn có chắc muốn kết thúc phiên học hiện tại?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.stop_button.setEnabled(False)

        def success(response):
            self.timer.stop()
            data = response.get("data") or {}
            self.timer_state = "IDLE"
            self.session_id = None
            self.current_phase = "FOCUS"
            self.remaining_seconds = self.focus_minutes * 60
            self.update_time_label()
            self.status_label.setText(
                response.get("message") or "Đã kết thúc phiên Pomodoro."
            )
            self.refresh_controls()

            summary = (
                f"Dự kiến: {data.get('plannedDurationSeconds', 0)} giây\n"
                f"Thực tế: {data.get('actualDurationSeconds', 0)} giây"
            )

            badges = data.get("newlyUnlockedBadges") or []
            if badges:
                badge_names = [
                    badge.get("badgeName", "Huy hiệu mới")
                    for badge in badges
                    if isinstance(badge, dict) and badge.get("isUnlocked", True)
                ]
                if badge_names:
                    summary += "\n\nHuy hiệu mới: " + ", ".join(badge_names)

            QMessageBox.information(self, "Kết quả phiên học", summary)
            self.session_stop.emit(data)

        def error(_response):
            self.stop_button.setEnabled(True)

        self.send_api(
            "/api/pomodoro/stop",
            "POMODORO_STOP",
            {"sessionId": self.session_id},
            success,
            error
        )

    # ĐẾM NGƯỢC VÀ CHUYỂN GIỮA HỌC / NGHỈ
    def _current_phase_duration(self):
        if self.current_phase == "FOCUS":
            return self.focus_minutes * 60
        return self.break_minutes * 60

    def update_countdown(self):
        if self.timer_state != "RUNNING":
            return

        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_time_label()

        if self.remaining_seconds <= 0:
            self.switch_phase()

    def switch_phase(self):
        if self.current_phase == "FOCUS":
            self.current_phase = "BREAK"
            self.remaining_seconds = self.break_minutes * 60
            self.phase_label.setText("THỜI GIAN NGHỈ")
            self.status_label.setText("Đã hết giờ tập trung. Hãy nghỉ ngơi một chút.")
        else:
            self.current_phase = "FOCUS"
            self.remaining_seconds = self.focus_minutes * 60
            self.phase_label.setText("THỜI GIAN TẬP TRUNG")
            self.status_label.setText("Hết giờ nghỉ. Bắt đầu phiên tập trung tiếp theo.")

        self.update_time_label()

    def update_time_label(self):
        minutes, seconds = divmod(max(0, self.remaining_seconds), 60)
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

        if self.current_phase == "FOCUS":
            self.phase_label.setText("THỜI GIAN TẬP TRUNG")
        else:
            self.phase_label.setText("THỜI GIAN NGHỈ")

    def refresh_controls(self):
        is_idle = self.timer_state == "IDLE"
        is_running = self.timer_state == "RUNNING"
        is_paused = self.timer_state == "PAUSED"

        self.start_button.setEnabled(is_idle)
        self.pause_button.setEnabled(is_running)
        self.resume_button.setEnabled(is_paused)
        self.stop_button.setEnabled(not is_idle)

        self.focus_spin.setEnabled(is_idle)
        self.break_spin.setEnabled(is_idle)
        self.save_settings_button.setEnabled(is_idle)

    # UC3: MINI-PLAYER
    def load_mini_player_preference(self):
        self.send_api(
            "/api/pomodoro/miniplayer/get",
            "POMODORO_GET_PREFERENCE",
            {},
            self.on_mini_player_preference_loaded
        )

    def on_mini_player_preference_loaded(self, response):
        data = response.get("data") or {}
        self.is_mini_player = bool(data.get("isMiniPlayer", False))
        self.apply_mini_player_mode()

    def toggle_mini_player(self):
        new_value = not self.is_mini_player
        self.mini_button.setEnabled(False)

        def apply_local_state():
            self.is_mini_player = new_value
            self.apply_mini_player_mode()
            self.mini_button.setEnabled(True)
            self.mini_player_toggled.emit(self.is_mini_player)

        def on_error(err_res):
            self.mini_button.setEnabled(True)
            if "404" in str(err_res.get("message", "")):
                apply_local_state()

        self.send_api(
            "/api/pomodoro/miniplayer/sync",
            "POMODORO_SYNC_PREFERENCE",
            {"isMiniPlayer": new_value},
            lambda _: apply_local_state(),
            on_error
        )

    def apply_mini_player_mode(self):
        if self.is_mini_player:
            self.header_widget.hide()
            self.status_label.hide()
            self.settings_card.hide()
            self.time_label.setStyleSheet("font-size: 44px;")
            self.mini_button.setText("Thoát")

            self.setParent(None)
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowStaysOnTopHint
            )
            self.resize(380, 220)
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.header_widget.show()
            self.status_label.show()
            self.settings_card.show()
            self.time_label.setStyleSheet("")
            self.mini_button.setText("Ghim")

            self.setWindowFlags(Qt.WindowType.Widget)

    # Xử lý case close toàn bộ app: gửi API Stop và thông báo cho MainWindow khi Backend xử lý xong.
    
    def stop_for_app_exit(self, on_success, on_error):
        if self.timer_state == "IDLE" or self.session_id is None:
            on_success()
            return

        self.stop_button.setEnabled(False)

        def success(response):
            data = response.get("data") or {}

            self.timer.stop()
            self.timer_state = "IDLE"
            self.session_id = None
            self.current_phase = "FOCUS"
            self.remaining_seconds = self.focus_minutes * 60

            self.update_time_label()
            self.refresh_controls()

            # Thông báo phiên học đã kết thúc
            self.session_stop.emit(data)

            # Báo cho MainWindow được phép đóng ứng dụng
            on_success()

        def error(response):
            self.stop_button.setEnabled(True)

            # API thất bại: không đóng ứng dụng
            on_error()

        self.send_api(
            "/api/pomodoro/stop",
            "POMODORO_STOP",
            {"sessionId": self.session_id},
            success,
            error
        )

    
    def closeEvent(self, event):
        # Nếu API Stop đã thành công và cho phép đóng cửa sổ
        if getattr(self, "_allow_close", False):
            event.accept()
            return

        # Nếu chưa có phiên Pomodoro thì đóng bình thường
        if self.timer_state == "IDLE" or self.session_id is None:
            self.timer.stop()
            event.accept()
            return

        # Hỏi xác nhận trước khi đóng cửa sổ
        confirm = QMessageBox.question(
            self,
            "Kết thúc phiên Pomodoro",
            "Bạn có muốn kết thúc phiên học hiện tại và đóng cửa sổ không?\n\n"
            "Thời gian học thực tế sẽ được ghi nhận.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        # Chọn ở lại
        if confirm != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        # Chọn xác nhận kết thúc phiên
        event.ignore()
        self.stop_button.setEnabled(False)

        def success(response):
            data = response.get("data") or {}

            # Chỉ dừng đồng hồ sau khi Backend xác nhận thành công
            self.timer.stop()
            self.timer_state = "IDLE"
            self.session_id = None
            self.current_phase = "FOCUS"
            self.remaining_seconds = self.focus_minutes * 60
            self.update_time_label()
            self.refresh_controls()

            # Cho phép đóng cửa sổ
            self._allow_close = True
            self.close()

            # Thông báo cho giao diện khác nếu cần cập nhật thống kê
            self.session_stop.emit(data)

        def error(_response):
            # API thất bại: giữ cửa sổ mở để không mất phiên học
            self.stop_button.setEnabled(True)

        self.send_api(
            "/api/pomodoro/stop",
            "POMODORO_STOP",
            {"sessionId": self.session_id},
            success,
            error
        )
