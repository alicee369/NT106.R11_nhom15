import random
from api_worker import APIWorker
from api_client import ClientPayloadBuilder

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

class RegisterWindow(QWidget):
    login_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Management - Đăng ký")
        self.setMinimumSize(800, 520)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Vùng trái: Thương hiệu
        left_panel = QFrame(objectName="leftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(18)

        left_layout.addWidget(QLabel("◈ StudyManagement", objectName="brandTitle"))
        left_layout.addStretch()
        left_layout.addWidget(QLabel("Build your\nlearning journey.", objectName="brandHeading"))
        desc = QLabel("Tạo không gian học tập của riêng bạn.\nBắt đầu lên kế hoạch và theo dõi tiến độ.", objectName="brandDescription")
        desc.setWordWrap(True)
        left_layout.addWidget(desc)
        left_layout.addStretch()

        # Vùng phải: Form đăng ký
        right_panel = QFrame(objectName="rightPanel")
        form_layout = QVBoxLayout(right_panel)
        form_layout.setContentsMargins(40, 28, 40, 28)
        form_layout.setSpacing(10)

        subtitle = QLabel("Điền thông tin để bắt đầu sử dụng.", objectName="formSubtitle")
        subtitle.setWordWrap(True)

        self.username_input = QLineEdit(placeholderText="Nhập tên đăng nhập")
        self.display_name_input = QLineEdit(placeholderText="Nhập tên hiển thị")
        self.password_input = QLineEdit(placeholderText="Nhập mật khẩu", echoMode=QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit(placeholderText="Nhập lại mật khẩu", echoMode=QLineEdit.EchoMode.Password)

        self.register_button = QPushButton("Tạo tài khoản", minimumHeight=44)
        self.register_button.clicked.connect(self.handle_register)

        login_text = QLabel('Đã có tài khoản? <a href="#">Đăng nhập</a>', objectName="registerText", alignment=Qt.AlignmentFlag.AlignCenter)
        login_text.setTextFormat(Qt.TextFormat.RichText)
        login_text.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        login_text.linkActivated.connect(lambda: self.login_requested.emit())

        form_layout.addStretch()
        form_layout.addWidget(QLabel("Tạo tài khoản", objectName="formTitle"))
        form_layout.addWidget(subtitle)
        form_layout.addSpacing(10)
        form_layout.addWidget(QLabel("Tên đăng nhập"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Tên hiển thị"))
        form_layout.addWidget(self.display_name_input)
        form_layout.addWidget(QLabel("Mật khẩu"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(QLabel("Nhập lại mật khẩu"))
        form_layout.addWidget(self.confirm_password_input)
        form_layout.addSpacing(5)
        form_layout.addWidget(self.register_button)
        form_layout.addWidget(login_text)
        form_layout.addStretch()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

        self.setStyleSheet("""
            QWidget { background-color: #0B1020; color: #F1F5F9; font-size: 14px; }
            QFrame#leftPanel { background-color: #111A30; border-right: 1px solid #27334D; }
            QFrame#rightPanel { background-color: #171D2E; }
            QLabel { background-color: transparent; }
            QLabel#brandTitle { color: #C4B5FD; font-size: 19px; font-weight: bold; }
            QLabel#brandHeading { color: #F8FAFC; font-size: 28px; font-weight: bold; }
            QLabel#brandDescription, QLabel#formSubtitle, QLabel#registerText { color: #94A3B8; font-size: 13px; }
            QLabel#formTitle { color: #F8FAFC; font-size: 25px; font-weight: bold; }
            QLabel#registerText a { color: #A78BFA; font-weight: bold; }
            QLineEdit { background-color: #0B1020; color: #F8FAFC; border: 1px solid #35415A; border-radius: 7px; padding: 9px; }
            QLineEdit:focus { border: 1px solid #8B5CF6; }
            QPushButton { background-color: #7C3AED; color: white; border: none; border-radius: 7px; font-weight: bold; }
            QPushButton:hover { background-color: #6D28D9; }
        """)

    def handle_register(self):
        username = self.username_input.text().strip()
        display_name = self.display_name_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not username or not display_name or not password or not confirm_password:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng điền đầy đủ tất cả các trường.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Mật khẩu không khớp", "Mật khẩu xác nhận không trùng khớp.")
            return

        req_id = random.randint(1000, 9999)
        payload = ClientPayloadBuilder.build_register_payload(req_id, username, password, display_name)
        url = "http://localhost:8000/api/auth/register"

        self.register_button.setEnabled(False)
        self.register_button.setText("Đang đăng ký...")

        self.worker = APIWorker(url, payload)
        self.worker.response_signal.connect(self.on_register_response)
        self.worker.error_signal.connect(self.on_register_error)
        self.worker.start()

    def on_register_response(self, response):
        self.register_button.setEnabled(True)
        self.register_button.setText("Tạo tài khoản")
        if response.get("success"):
            QMessageBox.information(self, "Thành công", response.get("message"))
            self.login_requested.emit()
        else:
            QMessageBox.critical(self, "Đăng ký thất bại", response.get("message"))

    def on_register_error(self, error_msg):
        self.register_button.setEnabled(True)
        self.register_button.setText("Tạo tài khoản")
        QMessageBox.critical(self, "Lỗi mạng", error_msg)