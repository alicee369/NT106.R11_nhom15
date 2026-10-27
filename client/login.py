import random
from api_worker import APIWorker
from api_client import ClientPayloadBuilder

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

class LoginWindow(QWidget):
    register_requested = Signal()
    login_success = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Management - Đăng nhập")
        self.setMinimumSize(800, 520)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Trái
        left_panel = QFrame(objectName="leftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(18)
        
        left_layout.addWidget(QLabel("◈ StudyManagement", objectName="brandTitle"))
        left_layout.addStretch()
        left_layout.addWidget(QLabel("Learn smarter.\nGrow further.", objectName="brandHeading"))
        desc = QLabel("Không gian học tập cá nhân của bạn.\nLập kế hoạch, quản lý và phát triển mỗi ngày.", objectName="brandDescription")
        desc.setWordWrap(True)
        left_layout.addWidget(desc)
        left_layout.addStretch()

        # Phải
        right_panel = QFrame(objectName="rightPanel")
        form_layout = QVBoxLayout(right_panel)
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(12)

        subtitle = QLabel("Đăng nhập để tiếp tục hành trình học tập.", objectName="formSubtitle")
        subtitle.setWordWrap(True)

        self.username_input = QLineEdit(placeholderText="Nhập tên đăng nhập")
        self.password_input = QLineEdit(placeholderText="Nhập mật khẩu", echoMode=QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton("Đăng nhập", minimumHeight=44)
        self.login_button.clicked.connect(self.handle_login)

        reg_link = QLabel('Chưa có tài khoản? <a href="#">Đăng ký</a>', objectName="registerText", alignment=Qt.AlignmentFlag.AlignCenter)
        reg_link.setTextFormat(Qt.TextFormat.RichText)
        reg_link.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        reg_link.linkActivated.connect(lambda: self.register_requested.emit())

        form_layout.addStretch()
        form_layout.addWidget(QLabel("Chào mừng trở lại!", objectName="formTitle"))
        form_layout.addWidget(subtitle)
        form_layout.addSpacing(20)
        form_layout.addWidget(QLabel("Tên đăng nhập"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Mật khẩu"))
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(8)
        form_layout.addWidget(self.login_button)
        form_layout.addWidget(reg_link)
        form_layout.addStretch()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

        self.setStyleSheet("""
            QWidget { background-color: #0B1020; color: #F1F5F9; font-size: 14px; }
            QFrame#leftPanel { background-color: #111A30; border-right: 1px solid #27334D; }
            QFrame#rightPanel { background-color: #171D2E; }
            QLabel { background-color: transparent; }
            QLabel#brandTitle { color: #C4B5FD; font-size: 19px; font-weight: bold; }
            QLabel#brandHeading { color: #F8FAFC; font-size: 30px; font-weight: bold; }
            QLabel#brandDescription, QLabel#formSubtitle, QLabel#registerText { color: #94A3B8; font-size: 13px; }
            QLabel#formTitle { color: #F8FAFC; font-size: 25px; font-weight: bold; }
            QLabel#registerText a { color: #A78BFA; font-weight: bold; }
            QLineEdit { background-color: #0B1020; color: #F8FAFC; border: 1px solid #35415A; border-radius: 7px; padding: 11px; }
            QLineEdit:focus { border: 1px solid #8B5CF6; }
            QPushButton { background-color: #7C3AED; color: white; border: none; border-radius: 7px; font-weight: bold; }
            QPushButton:hover { background-color: #6D28D9; }
        """)

    def handle_login(self):
        username, password = self.username_input.text().strip(), self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            return

        req_id = random.randint(1000, 9999)
        payload = ClientPayloadBuilder.build_login_payload(req_id, username, password)
        url = "http://localhost:8000/api/auth/login"

        self.login_button.setEnabled(False)
        self.login_button.setText("Đang đăng nhập...")

        self.worker = APIWorker(url, payload)
        self.worker.response_signal.connect(self.on_login_response)
        self.worker.error_signal.connect(self.on_login_error)
        self.worker.start()

    def on_login_response(self, response):
        print("Phản hồi đăng nhập từ server:", response) # tạm check để coi bug ở đâu

        self.login_button.setEnabled(True)
        self.login_button.setText("Đăng nhập")

        if response.get("success") is True:
            data = response.get("data")

            if not isinstance(data, dict):
                QMessageBox.critical(
                    self,
                    "Lỗi đăng nhập",
                    "Dữ liệu trả về từ máy chủ không hợp lệ."
                )
                return

            token = data.get("token")

            if not token:
                QMessageBox.critical(
                    self,
                    "Lỗi đăng nhập",
                    "Máy chủ không trả về token đăng nhập."
                )
                return

            self.login_success.emit(token)

        else:
            message = response.get(
                "message",
                "Tên đăng nhập hoặc mật khẩu không chính xác."
            )
            QMessageBox.warning(
                self,
                "Đăng nhập thất bại",
                message
            )

    def on_login_error(self, error_msg):
        self.login_button.setEnabled(True)
        self.login_button.setText("Đăng nhập")
        QMessageBox.critical(self, "Lỗi mạng", error_msg)