import random
from api_worker import APIWorker
from api_client import ClientPayloadBuilder
from update_profile import EditProfileWindow # tích hợp gd upadte_profile

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGridLayout, QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal

class ProfileWindow(QWidget):
    account_deleted = Signal()
    logged_out = Signal() #báo đx thành công

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
        logout_btn = QPushButton("Đăng xuất", clicked=self.handle_logout, styleSheet="background-color: #374151; color: white;")
        delete_btn = QPushButton("Xóa tài khoản", clicked=self.handle_delete_account, styleSheet="background-color: #DC2626; color: white;")
        close_btn = QPushButton("Đóng", clicked=self.close)

        footer_layout.addWidget(QLabel("Thông tin hồ sơ • Chế độ xem", objectName="footerNote"))
        footer_layout.addStretch()
        footer_layout.addWidget(update_btn)
        footer_layout.addWidget(logout_btn)
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
        self.worker.error_signal.connect(self.on_profile_error)
        self.worker.start()

    def on_profile_response(self, response):
        print("Phản hồi API hồ sơ:", response) # xem dl thực tế

        if response.get("success") is not True:
            QMessageBox.warning(
                self,
                "Không thể tải hồ sơ",
                response.get("message") or "Máy chủ không trả về thông tin hồ sơ."
            )
            return

        data = response.get("data")

        if not isinstance(data, dict):
            QMessageBox.warning(
                self,
                "Lỗi dữ liệu",
                "Dữ liệu hồ sơ trả về không hợp lệ."
            )
            return

        user_id = data.get("userId")
        username = data.get("username")
        display_name = data.get("displayName")
        join_date = data.get("joinDate")

        # Cập nhật tên hiển thị trên thẻ hồ sơ
        name = display_name or username or "Người dùng"
        self.full_name.setText(str(name))

        # Cập nhật chữ viết tắt trên avatar
        self.avatar.setText(str(name)[:2].upper())

        # Xóa các ô thông tin cũ trước khi tạo lại
        while self.info_grid.count():
            item = self.info_grid.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        # Hiển thị dữ liệu lấy từ API
        self.info_grid.addWidget(
            self.create_info_field(
                "Mã số người dùng (userId)",
                str(user_id) if user_id is not None else "Chưa có dữ liệu"
            ),
            0, 0
        )

        self.info_grid.addWidget(
            self.create_info_field(
                "Tên đăng nhập",
                str(username) if username else "Chưa có dữ liệu"
            ),
            0, 1
        )

        self.info_grid.addWidget(
            self.create_info_field(
                "Họ và tên hiển thị",
                str(display_name) if display_name else "Chưa có dữ liệu"
            ),
            1, 0
        )

        self.info_grid.addWidget(
            self.create_info_field(
                "Ngày tham gia hệ thống",
                str(join_date) if join_date else "Chưa có dữ liệu"
            ),
            1, 1
        )
    def on_profile_error(self, error_msg): # khi API không kết nối được hoặc xảy ra lỗi, sẽ biết lỗi cụ thể thay vì chỉ thấy một thông báo chung.
        self.full_name.setText("Không thể tải hồ sơ")

        QMessageBox.warning(
            self,
            "Lỗi tải hồ sơ",
            error_msg
        )
    
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
        # Mở cửa sổ EditProfileWindow chuyên nghiệp thay vì QInputDialog
        self.edit_window = EditProfileWindow(self.token)
        self.edit_window.profile_updated.connect(self.fetch_profile_data)  # Tự động làm mới dữ liệu khi cập nhật xong
        self.edit_window.show()

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

    def handle_logout(self):
        # UC24: Đăng xuất phiên làm việc
        confirm = QMessageBox.question(
            self,
            "Xác nhận đăng xuất",
            "Bạn có chắc chắn muốn kết thúc phiên làm việc?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        req_id = random.randint(1000, 9999)
        payload = {
            "action": "LOGOUT",
            "requestId": req_id,
            "data": {}
        }
        
        # 1. Gọi API logout tới server của Lam để xóa dữ liệu trên Supabase
        self.logout_worker = APIWorker("http://localhost:8000/api/auth/logout", payload, ClientPayloadBuilder.build_auth_header(self.token))
        
        def on_logout_success(res):
            if res.get("success"):
                QMessageBox.information(self, "Thông báo", res.get("message") or "Đăng xuất thành công!")
                
                # 2. Xóa sạch biến token lưu trữ ở máy
                self.token = None
                
                # Phát tín hiệu (nếu cần cho các component khác)
                self.logged_out.emit()
                
                # 3. Mở lại màn hình đăng nhập (Login) và đóng cửa sổ profile
                try:
                    from login import LoginWindow  # Thay đổi tên file/class login nếu nhóm dùng tên khác
                    self.login_window = LoginWindow()
                    self.login_window.show()
                except ImportError:
                    pass
                
                self.close()
            else:
                QMessageBox.critical(self, "Lỗi", res.get("message"))

        self.logout_worker.response_signal.connect(on_logout_success)
        self.logout_worker.error_signal.connect(lambda err: QMessageBox.critical(self, "Lỗi mạng", err))
        self.logout_worker.start()