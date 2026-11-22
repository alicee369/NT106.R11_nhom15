import sys
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, #chứa nhiều page, tại 1 thời điểm chỉ hiện 1 page, các page khác nằm chờ bên dưới
    QScrollArea, QFrame, QLabel, QPushButton, QMessageBox
)

from pomodoro import PomodoroWindow
from login import LoginWindow
from register import RegisterWindow
from profile import ProfileWindow 
from schedule import ScheduleWindow
from notes import NotesWindow
from reminders import RemindersWindow
from datetime import datetime, timezone, timedelta

# Trang khung tạm cho các chức năng chưa ghép UI hoàn chỉnh để dễ nối tiếp UC
class PlaceholderPage(QWidget):
    def __init__(self, title: str, subtitle: str, uc_tag: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        card = QFrame(objectName="contentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(10)

        lbl_uc = QLabel(uc_tag, objectName="headerTag")
        lbl_title = QLabel(title, objectName="pageTitle")
        lbl_desc = QLabel(subtitle, objectName="pageDescription")
        lbl_desc.setWordWrap(True)

        card_layout.addWidget(lbl_uc)
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_desc)
        card_layout.addStretch()

        layout.addWidget(card)


# [NEW] Màn hình menu chính sau khi đăng nhập, gồm thanh cuộn bên trái và khu vực hiển thị trang
class MainMenuPage(QWidget):
    """Màn hình menu chính sau khi đăng nhập, gồm thanh cuộn bên trái và QStackedWidget."""

    logged_out = Signal()
    account_deleted = Signal()

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.nav_buttons: dict[str, QPushButton] = {}
        self.pages: dict[str, QWidget] = {}

        self.notified_events: set[str] = set() #Lưu các thông báo đã hiển thị (key: "eventId_startTime") để không báo lặp lại

        self._build_ui()
        self.switch_page("dashboard")

        # Khởi động bộ đếm kiểm tra nhắc nhở mỗi 15 giây
        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(15000)
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start()

    def _build_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 📂 Thanh cuộn bên trái chứa các chức năng
        scroll_area = QScrollArea(objectName="sidebarScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFixedWidth(250)

        sidebar_widget = QWidget(objectName="sidebarContainer")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(14, 20, 14, 20)
        sidebar_layout.setSpacing(6)

        sidebar_layout.addWidget(QLabel("◈ StudyManagement", objectName="brandTitle"))
        sidebar_layout.addWidget(QLabel("Quản lý học tập", objectName="sidebarSub"))
        sidebar_layout.addSpacing(12)

        menu_items = [
            ("dashboard", "🏠  Trang chủ"),
            ("pomodoro", "⏱️  Pomodoro"),
            ("schedule", "📅  Lịch biểu"),
            ("notes", "📝  Ghi chú"),
            ("goals", "🎯  Mục tiêu - Kế hoạch"),
            ("statistics", "📊  Thống kê - GPA"),
            ("achievements", "🏅  Thành tựu - Huy hiệu"),
            ("community", "👥  Cộng đồng - BXH"),
            ("profile", "👤  Hồ sơ cá nhân"),
            ("reminders", "🔔  Nhắc nhở - Cài đặt"),
        ]

        for key, label in menu_items:
            btn = QPushButton(label, objectName="navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self.switch_page(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        sidebar_layout.addStretch()
        scroll_area.setWidget(sidebar_widget)
        root_layout.addWidget(scroll_area)

        # 🖥️ Khu vực nội dung bên phải
        right_panel = QWidget(objectName="mainArea")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        top_bar = QFrame(objectName="topBar")
        top_bar.setFixedHeight(58)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 0, 24, 0)

        self.section_label = QLabel("Trang chủ", objectName="topTitle")
        top_layout.addWidget(self.section_label)
        top_layout.addStretch()

        profile_shortcut = QPushButton("👤  Hồ sơ cá nhân", objectName="userChip")
        profile_shortcut.setCursor(Qt.CursorShape.PointingHandCursor)
        profile_shortcut.clicked.connect(lambda: self.switch_page("profile"))
        top_layout.addWidget(profile_shortcut)

        right_layout.addWidget(top_bar)

        self.page_stack = QStackedWidget(objectName="pageStack")
        right_layout.addWidget(self.page_stack)

        self._init_pages()
        root_layout.addWidget(right_panel, stretch=1)

    def _register_page(self, key: str, widget: QWidget):
        self.pages[key] = widget
        if self.page_stack.indexOf(widget) == -1:
            self.page_stack.addWidget(widget)

    def _init_pages(self):
        self._register_page(
            "dashboard",
            PlaceholderPage(
                title="Bảng tổng quan học tập",
                subtitle="Chọn một chức năng ở thanh bên trái để sử dụng Pomodoro, Lịch biểu, Ghi chú, Mục tiêu, Thống kê, Thành tựu, Cộng đồng hoặc Hồ sơ cá nhân.",
                uc_tag="TỔNG QUAN HỆ THỐNG",
            ),
        )

        self.pomodoro_page = PomodoroWindow(self.token)
        self.pomodoro_page.mini_player_toggled.connect(self._on_pomodoro_mini_toggled)
        self._register_page("pomodoro", self.pomodoro_page)

        self.schedule_page = ScheduleWindow(self.token)
        self.schedule_page.schedule_updated.connect(lambda _: self._check_reminders())
        self._register_page("schedule", self.schedule_page)
        self._register_page("notes", NotesWindow(self.token))

        self._register_page(
            "goals",
            PlaceholderPage(
                title="Mục tiêu & Kế hoạch học tập",
                subtitle="Thiết lập chiến dịch học tập cá nhân hóa và theo dõi tiến độ.",
                uc_tag="UC13 – UC15",
            ),
        )

        self._register_page(
            "statistics",
            PlaceholderPage(
                title="Thống kê trực quan & Ước lượng GPA",
                subtitle="Xem biểu đồ thời gian học và tính điểm mục tiêu học phần.",
                uc_tag="UC16, UC18",
            ),
        )

        self._register_page(
            "achievements",
            PlaceholderPage(
                title="Thành tựu & Huy hiệu",
                subtitle="Xem bộ sưu tập huy hiệu và chọn huy hiệu trưng bày trên hồ sơ.",
                uc_tag="UC17, UC28 – UC29",
            ),
        )

        self._register_page(
            "community",
            PlaceholderPage(
                title="Nhóm học tập & Bảng xếp hạng",
                subtitle="Tạo mã mời, tham gia nhóm học tập và xem bảng xếp hạng.",
                uc_tag="UC19 – UC21",
            ),
        )

        self.profile_window = ProfileWindow(self.token)
        self.profile_window.logged_out.connect(self.logged_out.emit)
        self.profile_window.account_deleted.connect(self.account_deleted.emit)
        self._register_page("profile", self.profile_window)

        self.reminders_page = RemindersWindow(self.token)
        self.reminders_page.config_updated.connect(self._on_reminder_config_changed)
        self._register_page("reminders", self.reminders_page)

    def switch_page(self, key: str):
        target = self.pages.get(key)
        if target is None:
            return

        if self.page_stack.indexOf(target) == -1:
            self.page_stack.addWidget(target)

        self.page_stack.setCurrentWidget(target)

        for nav_key, btn in self.nav_buttons.items():
            btn.setChecked(nav_key == key)

        active_btn = self.nav_buttons.get(key)
        if active_btn is not None:
            text = active_btn.text()
            self.section_label.setText(text.split("  ", 1)[-1] if "  " in text else text)

        if key == "profile" and hasattr(self.profile_window, "fetch_profile_data"):
            self.profile_window.fetch_profile_data()

    def _on_pomodoro_mini_toggled(self, is_mini: bool):
        if is_mini:
            if self.page_stack.currentWidget() is self.pomodoro_page:
                self.switch_page("dashboard")
            return

        self._register_page("pomodoro", self.pomodoro_page)
        self.switch_page("pomodoro")
        self.pomodoro_page.show()

        def _on_pomodoro_mini_toggled(self, is_mini: bool):
            if is_mini:
                if self.page_stack.currentWidget() is self.pomodoro_page:
                    self.switch_page("dashboard")
                return

            self._register_page("pomodoro", self.pomodoro_page)
            self.switch_page("pomodoro")
            self.pomodoro_page.show()

        def _on_reminder_config_changed(self, _new_config: dict):
            self.notified_events.clear()
            self._check_reminders()

        def _check_reminders(self):
            if not hasattr(self, "reminders_page") or not hasattr(self, "schedule_page"):
                return

            config = self.reminders_page.current_config
            events = self.schedule_page.events_cache
            now_utc = datetime.now(timezone.utc)

            for event in events:
                event_id = event.get("eventId")
                raw_start = event.get("startTime")
                event_type = str(event.get("eventType") or "STUDY").upper()
                title = str(event.get("title") or "Sự kiện")

                if not event_id or not raw_start:
                    continue

                if event_type == "DEADLINE":
                    rule = config.get("deadlineReminder", {})
                    type_label = "Deadline"
                else:
                    rule = config.get("studyReminder", {})
                    type_label = "Lịch thi" if event_type == "EXAM" else "Giờ học"

                if not rule.get("enabled", False):
                    continue

                notify_before = int(rule.get("notifyBeforeMinutes", 0))

                try:
                    cleaned = str(raw_start).replace("Z", "+00:00")
                    start_dt = datetime.fromisoformat(cleaned)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.astimezone()
                    start_utc = start_dt.astimezone(timezone.utc)
                except ValueError:
                    continue

                remind_time_utc = start_utc - timedelta(minutes=notify_before)

                if remind_time_utc <= now_utc <= start_utc:
                    notify_key = f"{event_id}_{raw_start}_{notify_before}"

                    if notify_key not in self.notified_events:
                        self.notified_events.add(notify_key)
                        local_time_str = start_utc.astimezone().strftime("%H:%M ngày %d/%m/%Y")

                        QMessageBox.information(
                            self,
                            f"🔔 Nhắc nhở {type_label}",
                            f"Sự kiện: {title}\n"
                            f"Thời gian diễn ra: {local_time_str}\n"
                            f"(Báo trước {notify_before} phút theo cài đặt của bạn)"
                        )

        def closeEvent(self, event):
            if hasattr(self, "reminder_timer"):
                self.reminder_timer.stop()
            super().closeEvent(event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self._allow_close = False #cho phép đóng ứng dụng sau khi API Stop thành công
        self._exit_stop_pending = False #tránh gửi nhiều yêu cầu Stop khi đang chờ Backend

        self.setWindowTitle("Study Management")
        self.resize(1100, 700) 
        self.setMinimumSize(860, 560)

        self.stacked_widget = QStackedWidget() # Nơi chứa các page

        # Tạo page login và reg
        self.login_page = LoginWindow() 
        self.register_page = RegisterWindow()  
        self.main_menu_page = None  # [NEW] Giữ tham chiếu tới màn hình menu chính sau đăng nhập

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.register_page)

        # Nhấn Đăng ký -> chuyển sang trang đăng ký
        self.login_page.register_requested.connect(
            lambda: self.stacked_widget.setCurrentIndex(1)
        )

        # Nhấn Đăng nhập -> quay lại trang đăng nhập
        self.register_page.login_requested.connect(
            lambda: self.stacked_widget.setCurrentIndex(0)
        )

        # Bắt tin hiệu login thành công từ LoginWindow để chạy hàm on_login_success
        self.login_page.login_success.connect(self.on_login_success)

        # Đặt stacked_widget vào layout 
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

        self.setLayout(layout)
        self._apply_menu_styles()  # [NEW] Áp dụng stylesheet cho thanh cuộn menu và các trang con

    # TỪ LOGIN SANG MAINMENUPAGE
    def on_login_success(self, token: str):
        if self.main_menu_page is not None:
            self.stacked_widget.removeWidget(self.main_menu_page)
            self.main_menu_page.deleteLater()
            self.main_menu_page = None

        self.main_menu_page = MainMenuPage(token)
        self.main_menu_page.logged_out.connect(self._reset_to_login)
        self.main_menu_page.account_deleted.connect(self._reset_to_login)

        self.stacked_widget.addWidget(self.main_menu_page)
        self.stacked_widget.setCurrentWidget(self.main_menu_page)
        self.resize(1140, 720)
        self.center_window()

        # CŨ: LOGIN->PROFILE
        # if hasattr(self, 'profile_page') and self.profile_page is not None: # Nếu profile đã tồn tại và có giá trị thì remove và delete tránh memory leak
        #     self.stacked_widget.removeWidget(self.profile_page)
        #     self.profile_page.deleteLater()

        # self.profile_page = ProfileWindow(token)  
        
        # # Xử lý case nếu tk bị xóa thì quay về login page
        # self.profile_page.account_deleted.connect(self.on_account_deleted)

        # #Xử lý case logout thì quay về login page
        # self.profile_page.logged_out.connect(self.on_logged_out)

        # self.stacked_widget.addWidget(self.profile_page)
        # self.stacked_widget.setCurrentWidget(self.profile_page)
        # self.resize(960, 640)  
        # self.center_window()

    # [NEW] Hàm dùng chung để dọn phiên hiện tại và quay lại màn hình đăng nhập
    def _reset_to_login(self):
        self.login_page.username_input.clear()
        self.login_page.password_input.clear()
        self.stacked_widget.setCurrentIndex(0)

        if self.main_menu_page is not None:
            self.stacked_widget.removeWidget(self.main_menu_page)
            self.main_menu_page.deleteLater()
            self.main_menu_page = None

        self.resize(960, 600)
        self.center_window()

    # Xử lý case đóng toàn bộ ứng dụng
    def closeEvent(self, event):

        # Nếu đã xác nhận và API Stop thành công
        if self._allow_close:
            event.accept()
            return

        # Tránh gửi nhiều yêu cầu Stop cùng lúc
        if self._exit_stop_pending:
            event.ignore()
            return

        # Chưa đăng nhập
        if self.main_menu_page is None:
            event.accept()
            return

        pomodoro = self.main_menu_page.pomodoro_page

        # Không có phiên Pomodoro đang chạy
        if pomodoro.timer_state == "IDLE" or pomodoro.session_id is None:
            pomodoro.close()
            event.accept()
            return

        # Hỏi xác nhận trước khi thoát
        confirm = QMessageBox.question(
            self,
            "Thoát Study Management",
            "Bạn đang có phiên Pomodoro chưa kết thúc.\n\n"
            "Bạn có muốn kết thúc phiên học, ghi nhận thời gian "
            "và thoát ứng dụng không?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        event.ignore()
        self._exit_stop_pending = True

        def on_stop_success():
            self._exit_stop_pending = False
            self._allow_close = True

            # Đóng cả cửa sổ Pomodoro nếu đang ở Mini-player
            pomodoro.close()

            # Đóng toàn bộ ứng dụng
            self.close()

        def on_stop_error():
            self._exit_stop_pending = False

        pomodoro.stop_for_app_exit(
            on_stop_success,
            on_stop_error
        )

    # def on_logged_out(self):
    #     # Nhận tín hiệu emit ở profile.py và xóa thông tin đăng nhập
    #     self.login_page.username_input.clear()
    #     self.login_page.password_input.clear()

    #     # Quay về login page
    #     self.stacked_widget.setCurrentIndex(0)
    #     self.resize(960, 600)
    #     self.center_window()

    # def on_account_deleted(self):
    #     self.login_page.username_input.clear()
    #     self.login_page.password_input.clear()
        
    #     self.stacked_widget.setCurrentIndex(0)
    #     self.resize(960, 600)
    #     self.center_window()

    # Xử lý lỗi để tự động canh cửa sổ ra center màn hình
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    # [NEW] Định dạng giao diện cho sidebar cuộn, nút điều hướng, thanh header và thẻ nội dung
    def _apply_menu_styles(self):
        self.setStyleSheet(
            self.styleSheet()
            + """
            QScrollArea#sidebarScroll {
                background-color: #11182C;
                border: none;
                border-right: 1px solid #222E47;
            }
            QWidget#sidebarContainer, QWidget#mainArea, QWidget#pageStack {
                background-color: #0B1020;
            }
            QWidget#sidebarContainer {
                background-color: #11182C;
            }
            QScrollBar:vertical {
                background: #11182C;
                width: 8px;
                margin: 4px 2px 4px 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #2D3A56;
                min-height: 28px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QLabel#sidebarSub {
                color: #94A3B8;
                font-size: 12px;
            }
            QPushButton#navButton {
                text-align: left;
                padding: 10px 12px;
                border-radius: 8px;
                border: 1px solid transparent;
                background-color: transparent;
                color: #CBD5E1;
                font-weight: 600;
            }
            QPushButton#navButton:hover {
                background-color: #1A243D;
                color: #F8FAFC;
            }
            QPushButton#navButton:checked {
                background-color: #6D3CCB;
                border: 1px solid #8055D9;
                color: #FFFFFF;
            }
            QFrame#topBar {
                background-color: #11182C;
                border-bottom: 1px solid #222E47;
            }
            QLabel#topTitle {
                color: #F8FAFC;
                font-size: 17px;
                font-weight: bold;
            }
            QPushButton#userChip {
                background-color: #171D2E;
                border: 1px solid #2E3B57;
                border-radius: 16px;
                padding: 6px 14px;
                color: #E2E8F0;
                font-weight: 600;
            }
            QPushButton#userChip:hover {
                border-color: #8055D9;
                background-color: #1E273E;
            }
            QFrame#contentCard {
                background-color: #171D2E;
                border: 1px solid #28334B;
                border-radius: 15px;
            }
            QLabel#headerTag {
                color: #A78BFA;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QLabel#pageTitle {
                color: #F8FAFC;
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#pageDescription {
                color: #94A3B8;
                font-size: 13px;
            }
            """
        )
        
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())