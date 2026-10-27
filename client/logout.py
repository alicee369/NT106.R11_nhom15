import random
from api_worker import APIWorker
from api_client import ClientPayloadBuilder
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal

class LogoutDialog(QDialog):
    logout_success = Signal()

    def __init__(self, token: str):
        super().__init__()
        self.token = token
        self.setWindowTitle("Study Management - Đăng xuất")
        self.setFixedSize(420, 270)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 25, 28, 25)
        layout.setSpacing(14)

        icon_label = QLabel("↗", objectName="iconLabel", alignment=Qt.AlignmentFlag.AlignCenter, fixedSize=(48, 48))
        title = QLabel("Đăng xuất khỏi tài khoản?", objectName="dialogTitle", alignment=Qt.AlignmentFlag.AlignCenter)
        message = QLabel("Bạn có chắc chắn muốn đăng xuất khỏi\nStudy Management không?", objectName="dialogMessage", alignment=Qt.AlignmentFlag.AlignCenter, wordWrap=True)

        cancel_button = QPushButton("Ở lại", objectName="cancelButton", minimumHeight=40)
        cancel_button.clicked.connect(self.reject)

        self.logout_button = QPushButton("Đăng xuất", objectName="logoutButton", minimumHeight=40)
        self.logout_button.clicked.connect(self.handle_logout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addWidget(cancel_button)
        btn_layout.addWidget(self.logout_button)

        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QDialog { background-color: #111827; }
            QLabel { background-color: transparent; }
            QLabel#iconLabel { background-color: #292044; color: #C4B5FD; font-size: 26px; font-weight: bold; border-radius: 24px; }
            QLabel#dialogTitle { color: #F8FAFC; font-size: 19px; font-weight: bold; }
            QLabel#dialogMessage { color: #94A3B8; font-size: 13px; }
            QPushButton { border: none; border-radius: 7px; padding: 9px; font-size: 13px; font-weight: bold; }
            QPushButton#cancelButton { background-color: #263248; color: #E2E8F0; }
            QPushButton#cancelButton:hover { background-color: #35435D; }
            QPushButton#logoutButton { background-color: #7C3AED; color: white; }
            QPushButton#logoutButton:hover { background-color: #6D28D9; }
        """)

    def handle_logout(self):
        req_id = random.randint(1000, 9999)
        # Payload chuẩn UC24
        payload = {
            "action": "AUTH_LOGOUT",
            "requestId": req_id,
            "data": {}
        }
        headers = ClientPayloadBuilder.build_auth_header(self.token)
        url = "http://localhost:5000/api/auth/logout"

        self.logout_button.setEnabled(False)
        self.logout_button.setText("Đang đăng xuất...")

        self.worker = APIWorker(url, payload, headers)
        self.worker.response_signal.connect(self.on_logout_response)
        self.worker.error_signal.connect(self.on_logout_error)
        self.worker.start()

    def on_logout_response(self, response):
        if response.get("success"):
            self.logout_success.emit()
            self.accept()
        else:
            self.logout_button.setEnabled(True)
            self.logout_button.setText("Đăng xuất")

    def on_logout_error(self, _):
        self.logout_success.emit()
        self.accept()