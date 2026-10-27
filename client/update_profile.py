pip install sqlmodel psycopg2-binaryimport random
from api_worker import APIWorker
from api_client import ClientPayloadBuilder

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal


class EditProfileWindow(QWidget):
    profile_updated = Signal() # tạo tín hiệu báo cập nhật thành công

    def __init__(self, token: str):
        super().__init__()
        self.token = token  # Nhận token phiên làm việc từ MainWindow gửi sang

        # Cấu hình cửa sổ
        self.setWindowTitle("Study Management - Cập nhật hồ sơ")
        self.resize(900, 750)
        self.setMinimumSize(800, 600)

        # Bố cục ngoài cùng cho cửa sổ chính chứa ScrollArea
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Tạo QScrollArea để chống tràn/đè chữ khi thu nhỏ cửa sổ
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        # Container widget chứa toàn bộ nội dung bên trong scroll
        container_widget = QWidget()
        container_widget.setObjectName("containerWidget")
        
        # =========================
        # BỐ CỤC CHÍNH BÊN TRONG
        # =========================
        main_layout = QVBoxLayout(container_widget)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(16)

        # =========================
        # THANH ĐẦU TRANG
        # =========================
        header_layout = QHBoxLayout()

        self.brand_title = QLabel("◈ StudyManagement")
        self.brand_title.setObjectName("brandTitle")

        self.header_note = QLabel("HỒ SƠ CÁ NHÂN / CHỈNH SỬA")
        self.header_note.setObjectName("headerNote")

        header_layout.addWidget(self.brand_title)
        header_layout.addStretch()
        header_layout.addWidget(self.header_note)

        # =========================
        # TIÊU ĐỀ
        # =========================
        self.page_title = QLabel("Cập nhật thông tin")
        self.page_title.setObjectName("pageTitle")

        self.page_description = QLabel(
            "Thay đổi thông tin hiển thị hoặc cập nhật mật khẩu tài khoản."
        )
        self.page_description.setObjectName("pageDescription")
        self.page_description.setWordWrap(True)

        # =========================
        # THẺ THÔNG TIN CÁ NHÂN
        # =========================
        info_card = QFrame()
        info_card.setObjectName("formCard")

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(8)

        self.info_title = QLabel("Thông tin cá nhân")
        self.info_title.setObjectName("sectionTitle")

        self.name_label = QLabel("Tên hiển thị mới")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên hiển thị mới")

        info_layout.addWidget(self.info_title)
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.name_input)

        info_card.setLayout(info_layout)

        # =========================
        # THẺ ĐỔI MẬT KHẨU
        # =========================
        password_card = QFrame()
        password_card.setObjectName("formCard")

        password_layout = QVBoxLayout()
        password_layout.setContentsMargins(20, 16, 20, 16)
        password_layout.setSpacing(8)

        self.password_title = QLabel("Đổi mật khẩu")
        self.password_title.setObjectName("sectionTitle")

        self.current_password_label = QLabel("Mật khẩu hiện tại")
        self.current_password_input = QLineEdit()
        self.current_password_input.setPlaceholderText(
            "Nhập mật khẩu hiện tại"
        )
        self.current_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.new_password_label = QLabel("Mật khẩu mới")
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText(
            "Nhập mật khẩu mới"
        )
        self.new_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.confirm_password_label = QLabel(
            "Xác nhận mật khẩu mới"
        )
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText(
            "Nhập lại mật khẩu mới"
        )
        self.confirm_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        password_layout.addWidget(self.password_title)
        password_layout.addWidget(self.current_password_label)
        password_layout.addWidget(self.current_password_input)
        password_layout.addWidget(self.new_password_label)
        password_layout.addWidget(self.new_password_input)
        password_layout.addWidget(self.confirm_password_label)
        password_layout.addWidget(self.confirm_password_input)

        password_card.setLayout(password_layout)

        # =========================
        # CÁC NÚT CHỨC NĂNG
        # =========================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.cancel_button = QPushButton("Hủy")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setMinimumSize(110, 38)
        self.cancel_button.clicked.connect(self.close)

        self.save_button = QPushButton("Lưu thay đổi")
        self.save_button.setObjectName("saveButton")
        self.save_button.setMinimumSize(140, 38)
        self.save_button.clicked.connect(self.handle_save)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        # =========================
        # GHÉP BỐ CỤC VÀO CONTAINER
        # =========================
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.page_title)
        main_layout.addWidget(self.page_description)
        main_layout.addWidget(info_card)
        main_layout.addWidget(password_card)
        main_layout.addLayout(button_layout)

        scroll_area.setWidget(container_widget)
        outer_layout.addWidget(scroll_area)

        # =========================
        # ĐỊNH DẠNG GIAO DIỆN
        # =========================
        self.setStyleSheet("""
            QWidget {
                background-color: #0B1020;
                color: #F1F5F9;
                font-size: 13px;
            }
            QLabel {
                background-color: transparent;
            }
            QLabel#brandTitle {
                color: #C4B5FD;
                font-size: 19px;
                font-weight: bold;
            }
            QLabel#headerNote {
                color: #94A3B8;
                font-size: 11px;
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
            QFrame#formCard {
                background-color: #171D2E;
                border: 1px solid #28334B;
                border-radius: 10px;
            }
            QLabel#sectionTitle {
                color: #F8FAFC;
                font-size: 15px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #0B1020;
                color: #F8FAFC;
                border: 1px solid #35415A;
                border-radius: 6px;
                padding: 7px 10px;
                min-height: 26px;
            }
            QLineEdit:focus {
                border: 1px solid #8B5CF6;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton#cancelButton {
                background-color: #263248;
                color: #E2E8F0;
                border: 1px solid #35415A;
            }
            QPushButton#cancelButton:hover {
                background-color: #35435D;
            }
            QPushButton#saveButton {
                background-color: #7C3AED;
                color: white;
            }
            QPushButton#saveButton:hover {
                background-color: #6D28D9;
            }
            QScrollBar:vertical {
                border: none;
                background: #0B1020;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #27334D;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def handle_save(self):
        display_name = self.name_input.text().strip()
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not display_name:
            self.show_message("Thiếu thông tin", "Vui lòng nhập tên hiển thị mới.", QMessageBox.Icon.Warning)
            return

        # Kiểm tra tính hợp lệ nếu người dùng nhập thông tin đổi mật khẩu
        if current_password or new_password or confirm_password:
            if not current_password:
                self.show_message("Thiếu thông tin", "Vui lòng nhập mật khẩu hiện tại để xác thực.", QMessageBox.Icon.Warning)
                return
            if not new_password:
                self.show_message("Thiếu thông tin", "Vui lòng nhập mật khẩu mới.", QMessageBox.Icon.Warning)
                return
            if new_password != confirm_password:
                self.show_message("Mật khẩu không khớp", "Mật khẩu mới và xác nhận nhập lại không trùng khớp.", QMessageBox.Icon.Warning)
                return

        # Đóng gói dữ liệu payload UC26 gửi lên server
        req_id = random.randint(1000, 9999)
        payload = {
            "action": "PROFILE_UPDATE",
            "requestId": req_id,
            "data": {
                "displayName": display_name,
                "oldPassword": current_password,
                "newPassword": new_password
            }
        }
        headers = ClientPayloadBuilder.build_auth_header(self.token)
        url = "http://localhost:8000/api/profile/update"

        self.save_button.setEnabled(False)
        self.save_button.setText("Đang lưu...")

        self.worker = APIWorker(url, payload, headers)
        self.worker.response_signal.connect(self.on_update_response)
        self.worker.error_signal.connect(self.on_update_error)
        self.worker.start()

    def on_update_response(self, response):
        self.save_button.setEnabled(True)
        self.save_button.setText("Lưu thay đổi")

        if response.get("success"):
            self.show_message("Thành công", response.get("message", "Cập nhật hồ sơ thành công."), QMessageBox.Icon.Information)
            self.profile_updated.emit() #phát signal báo thành công
            self.close()
        else:
            self.show_message("Thất bại", response.get("message"), QMessageBox.Icon.Critical)

    def on_update_error(self, error_msg):
        self.save_button.setEnabled(True)
        self.save_button.setText("Lưu thay đổi")
        self.show_message("Lỗi kết nối", error_msg, QMessageBox.Icon.Critical)

    def show_message(self, title, message, icon):
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { background-color: transparent; color: #1F2937; font-size: 14px; }
            QPushButton { background-color: #7C3AED; color: white; border: none; border-radius: 6px; padding: 6px 18px; font-weight: bold; }
            QPushButton:hover { background-color: #6D28D9; }
        """)
        msg.exec()