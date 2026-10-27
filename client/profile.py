import random
from api_worker import APIWorker
from api_client import ClientPayloadBuilder

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGridLayout, QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal

class ProfileWindow(QWidget):
    account_deleted = Signal()

    def __init__(self, token: str):
        super().__init__()
        self.token = token
        self.setWindowTitle("Study Management - Hồ sơ cá nhân")
        self.resize(960, 640)
        self.setMinimumSize(800, 560)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 26, 32, 26)
        main_layout.setSpacing(22)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("◈ StudyManagement", objectName="brandTitle"))
        header_layout.addStretch()
        header_layout.addWidget(QLabel("●  Tài khoản cá nhân", objectName="accountStatus"))

        main_layout.addLayout(header_layout)
        main_layout.addWidget(QLabel("Hồ sơ cá nhân", objectName="pageTitle"))
        main_layout.addWidget(QLabel("Xem thông tin tài khoản và hồ sơ cá nhân của bạn.", objectName="pageDescription"))

        # Profile Card
        profile_card = QFrame(objectName="profileCard")
        profile_layout = QHBoxLayout(profile_card)
        profile_layout.setContentsMargins(24, 24, 24, 24)
        profile_layout.setSpacing(20)

        self.avatar = QLabel("??", objectName="avatar")
        self.avatar.setFixedSize(82, 82)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(7)
        self.full_name = QLabel("Đang tải thông tin...", objectName="fullName")
        user_info_layout.addWidget(self.full_name)
        user_info_layout.addWidget(QLabel("Thành viên StudyManagement", objectName="userRole"))
        user_info_layout.addWidget(QLabel("Hồ sơ người dùng", objectName="profileNote"))
        user_info_layout.addStretch()

        profile_layout.addWidget(self.avatar)
        profile_layout.addLayout(user_info_layout)
        profile_layout.addStretch()
        main_layout.addWidget(profile_card)

        # Details Card
        details_card = QFrame(objectName="detailsCard")
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(24, 24, 24, 24)
        details_layout.setSpacing(18)

        details_layout.addWidget(QLabel("Thông tin cá nhân", objectName="detailsTitle"))
        details_layout.addWidget(QLabel("Các thông tin hiện có trong hồ sơ của bạn.", objectName="detailsSubtitle"))

        self.info_grid = QGridLayout()
        self.info_grid.setHorizontalSpacing(24)
        self.info_grid.setVerticalSpacing(20)
        details_layout.addLayout(self.info_grid)
        details_layout.addStretch()
        main_layout.addWidget(details_card, 1)

        # Footer & Action Buttons
        footer_layout = QHBoxLayout()
        update_btn = QPushButton("Cập nhật hồ sơ", clicked=self.handle_update_prompt)
        delete_btn = QPushButton("Xóa tài khoản", clicked=self.handle_delete_account, styleSheet="background-color: #DC2626; color: white;")
        close_btn = QPushButton("Đóng", clicked=self.close)

        footer_layout.addWidget(QLabel("Thông tin hồ sơ • Chế độ xem", objectName="footerNote"))
        footer_layout.addStretch()
        footer_layout.addWidget(update_btn)
        footer_layout.addWidget(delete_btn)
        footer_layout.addWidget(close_btn)
        main_layout.addLayout(footer_layout)

        self.setStyleSheet("""
            QWidget { background-color: #0B1020; color: #F1F5F9; font-size: 14px; }
            QLabel { background-color: transparent; }
            QLabel#brandTitle { color: #C4B5FD; font-size: 20px; font-weight: bold; }
            QLabel#accountStatus { color: #A78BFA; font-size: 12px; }
            QLabel#pageTitle { color: #F8FAFC; font-size: 28px; font-weight: bold; }
            QLabel#pageDescription, QLabel#detailsSubtitle, QLabel#footerNote { color: #94A3B8; font-size: 12px; }
            QFrame#profileCard, QFrame#detailsCard { background-color: #171D2E; border: 1px solid #28334B; border-radius: 14px; }
            QLabel#avatar { background-color: #35245C; color: #DDD6FE; border: 1px solid #6245A5; border-radius: 41px; font-size: 23px; font-weight: bold; }
            QLabel#fullName { color: #F8FAFC; font-size: 22px; font-weight: bold; }
            QLabel#userRole { color: #C4B5FD; font-size: 13px; }
            QLabel#profileNote { color: #94A3B8; font-size: 12px; }
            QLabel#detailsTitle { color: #F8FAFC; font-size: 19px; font-weight: bold; }
            QPushButton { background-color: #263248; color: #E2E8F0; border: 1px solid #35415A; border-radius: 8px; font-weight: bold; padding: 8px 16px; }
            QPushButton:hover { background-color: #35435D; }
        """)

        self.fetch_profile_data()

    def fetch_profile_data(self):
        req_id = random.randint(1000, 9999)
        # Payload chuẩn UC25
        payload = {
            "action": "PROFILE_GET",
            "requestId": req_id,
            "data": {}
        }
        self.worker = APIWorker("http://localhost:8000/api/profile", payload, ClientPayloadBuilder.build_auth_header(self.token))
        self.worker.response_signal.connect(self.on_profile_response)
        self.worker.error_signal.connect(lambda _: self.full_name.setText("Mất kết nối máy chủ"))
        self.worker.start()

    def on_profile_response(self, response):
        if response.get("success"):
            data = response.get("data", {})
            user_id, username, display_name, join_date = data.get("userId"), data.get("username"), data.get("displayName"), data.get("joinDate")

            self.full_name.setText(display_name or username)
            self.avatar.setText((display_name or username)[:2].upper())

            while self.info_grid.count():
                widget = self.info_grid.takeAt(0).widget()
                if widget: widget.deleteLater()

            self.info_grid.addWidget(self.create_info_field("Mã số người dùng (userId)", str(user_id)), 0, 0)
            self.info_grid.addWidget(self.create_info_field("Tên đăng nhập", username), 0, 1)
            self.info_grid.addWidget(self.create_info_field("Họ và tên hiển thị", display_name), 1, 0)
            self.info_grid.addWidget(self.create_info_field("Ngày tham gia hệ thống", str(join_date)), 1, 1)

    def create_info_field(self, label_text, value_text):
        field = QFrame(styleSheet="QFrame { background-color: #0F172A; border: 1px solid #303B53; border-radius: 9px; }")
        field.setMinimumHeight(88)
        layout = QVBoxLayout(field)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        layout.addWidget(QLabel(label_text, styleSheet="color: #94A3B8; font-size: 12px; border: none; background: transparent;"))
        layout.addWidget(QLabel(value_text, styleSheet="color: #F8FAFC; font-size: 14px; font-weight: bold; border: none; background: transparent;", wordWrap=True))
        layout.addStretch()
        return field

    def handle_update_prompt(self):
        # UC26: Cập nhật thông tin cá nhân
        new_name, ok = QInputDialog.getText(self, "Cập nhật hồ sơ", "Tên hiển thị mới:")
        if not ok: return
        old_pass, ok2 = QInputDialog.getText(self, "Xác nhận mật khẩu", "Mật khẩu cũ:", QLineEdit.EchoMode.Password)
        if not ok2: return
        new_pass, ok3 = QInputDialog.getText(self, "Mật khẩu mới", "Mật khẩu mới:", QLineEdit.EchoMode.Password)
        if not ok3: return

        req_id = random.randint(1000, 9999)
        payload = {
            "action": "PROFILE_UPDATE",
            "requestId": req_id,
            "data": {
                "displayName": new_name,
                "oldPassword": old_pass,
                "newPassword": new_pass
            }
        }
        self.update_worker = APIWorker("http://localhost:8000/api/profile/update", payload, ClientPayloadBuilder.build_auth_header(self.token))
        self.update_worker.response_signal.connect(lambda res: [QMessageBox.information(self, "Thông báo", res.get("message")), self.fetch_profile_data() if res.get("success") else None])
        self.update_worker.error_signal.connect(lambda err: QMessageBox.critical(self, "Lỗi", err))
        self.update_worker.start()

    def handle_delete_account(self):
        # UC27: Xóa tài khoản
        password, ok = QInputDialog.getText(self, "Xóa tài khoản vĩnh viễn", "Nhập mật khẩu để xác nhận xóa:", QLineEdit.EchoMode.Password)
        if not ok or not password: return

        req_id = random.randint(1000, 9999)
        payload = {
            "action": "PROFILE_DELETE",
            "requestId": req_id,
            "data": {
                "passwordToConfirm": password
            }
        }
        self.delete_worker = APIWorker("http://localhost:8000/api/profile/delete", payload, ClientPayloadBuilder.build_auth_header(self.token))
        self.delete_worker.response_signal.connect(lambda res: [QMessageBox.information(self, "Thông báo", res.get("message")), self.account_deleted.emit(), self.close()] if res.get("success") else QMessageBox.critical(self, "Lỗi", res.get("message")))
        self.delete_worker.error_signal.connect(lambda err: QMessageBox.critical(self, "Lỗi mạng", err))
        self.delete_worker.start()