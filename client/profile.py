
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGridLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt


class ProfileWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Cấu hình cửa sổ
        self.setWindowTitle("Study Management - Hồ sơ cá nhân")
        self.resize(960, 640)
        self.setMinimumSize(800, 560)

        # =========================
        # BỐ CỤC CHÍNH
        # =========================
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(32, 26, 32, 26)
        main_layout.setSpacing(22)

        # =========================
        # THANH ĐẦU TRANG
        # =========================
        header_layout = QHBoxLayout()

        self.brand_title = QLabel("◈ StudyManagement")
        self.brand_title.setObjectName("brandTitle")

        self.account_status = QLabel("●  Tài khoản cá nhân")
        self.account_status.setObjectName("accountStatus")

        header_layout.addWidget(self.brand_title)
        header_layout.addStretch()
        header_layout.addWidget(self.account_status)

        # =========================
        # TIÊU ĐỀ TRANG
        # =========================
        self.page_title = QLabel("Hồ sơ cá nhân")
        self.page_title.setObjectName("pageTitle")

        self.page_description = QLabel(
            "Xem thông tin tài khoản và hồ sơ cá nhân của bạn."
        )
        self.page_description.setObjectName("pageDescription")
        self.page_description.setWordWrap(True)

        # =========================
        # THẺ THÔNG TIN NGƯỜI DÙNG
        # =========================
        profile_card = QFrame()
        profile_card.setObjectName("profileCard")

        profile_layout = QHBoxLayout()
        profile_layout.setContentsMargins(24, 24, 24, 24)
        profile_layout.setSpacing(20)

        # Ảnh đại diện minh họa bằng biểu tượng
        self.avatar = QLabel("NA")
        self.avatar.setObjectName("avatar")
        self.avatar.setFixedSize(82, 82)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tên và vai trò
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(7)

        self.full_name = QLabel("Nguyễn Văn A")
        self.full_name.setObjectName("fullName")

        self.user_role = QLabel("Thành viên StudyManagement")
        self.user_role.setObjectName("userRole")

        self.profile_note = QLabel("Hồ sơ người dùng")
        self.profile_note.setObjectName("profileNote")

        user_info_layout.addWidget(self.full_name)
        user_info_layout.addWidget(self.user_role)
        user_info_layout.addWidget(self.profile_note)
        user_info_layout.addStretch()

        profile_layout.addWidget(self.avatar)
        profile_layout.addLayout(user_info_layout)
        profile_layout.addStretch()

        profile_card.setLayout(profile_layout)

        # =========================
        # THẺ THÔNG TIN CÁ NHÂN
        # =========================
        details_card = QFrame()
        details_card.setObjectName("detailsCard")

        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(24, 24, 24, 24)
        details_layout.setSpacing(18)

        self.details_title = QLabel("Thông tin cá nhân")
        self.details_title.setObjectName("detailsTitle")

        self.details_subtitle = QLabel(
            "Các thông tin hiện có trong hồ sơ của bạn."
        )
        self.details_subtitle.setObjectName("detailsSubtitle")
        self.details_subtitle.setWordWrap(True)

        # Bố trí thông tin thành hai cột
        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(24)
        info_grid.setVerticalSpacing(20)

        # Dữ liệu minh họa, chưa kết nối cơ sở dữ liệu
        self.username_value = self.create_info_field(
            "Tên đăng nhập", "nguyenvana"
        )

        self.name_value = self.create_info_field(
            "Họ và tên", "Nguyễn Văn A"
        )

        self.email_value = self.create_info_field(
            "Email", "vana@example.com"
        )

        self.join_date_value = self.create_info_field(
            "Ngày tham gia", "01/10/2026"
        )

        info_grid.addWidget(self.username_value, 0, 0)
        info_grid.addWidget(self.name_value, 0, 1)
        info_grid.addWidget(self.email_value, 1, 0)
        info_grid.addWidget(self.join_date_value, 1, 1)

        details_layout.addWidget(self.details_title)
        details_layout.addWidget(self.details_subtitle)
        details_layout.addSpacing(4)
        details_layout.addLayout(info_grid)
        details_layout.addStretch()

        details_card.setLayout(details_layout)
        details_card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # =========================
        # CHÂN TRANG
        # =========================
        footer_layout = QHBoxLayout()

        self.footer_note = QLabel(
            "Thông tin hồ sơ • Chế độ xem"
        )
        self.footer_note.setObjectName("footerNote")

        self.back_button = QPushButton("Đóng")
        self.back_button.setObjectName("backButton")
        self.back_button.setMinimumSize(110, 40)

        # Đóng cửa sổ giao diện hiện tại
        self.back_button.clicked.connect(self.close)

        footer_layout.addWidget(self.footer_note)
        footer_layout.addStretch()
        footer_layout.addWidget(self.back_button)

        # =========================
        # GHÉP CÁC THÀNH PHẦN
        # =========================
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.page_title)
        main_layout.addWidget(self.page_description)
        main_layout.addWidget(profile_card)
        main_layout.addWidget(details_card, 1)
        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

        # =========================
        # ĐỊNH DẠNG GIAO DIỆN
        # =========================
        self.setStyleSheet("""
            QWidget {
                background-color: #0B1020;
                color: #F1F5F9;
                font-size: 14px;
            }

            QLabel {
                background-color: transparent;
            }

            QLabel#brandTitle {
                color: #C4B5FD;
                font-size: 20px;
                font-weight: bold;
            }

            QLabel#accountStatus {
                color: #A78BFA;
                font-size: 12px;
            }

            QLabel#pageTitle {
                color: #F8FAFC;
                font-size: 28px;
                font-weight: bold;
            }

            QLabel#pageDescription {
                color: #94A3B8;
                font-size: 13px;
            }

            QFrame#profileCard,
            QFrame#detailsCard {
                background-color: #171D2E;
                border: 1px solid #28334B;
                border-radius: 14px;
            }

            QLabel#avatar {
                background-color: #35245C;
                color: #DDD6FE;
                border: 1px solid #6245A5;
                border-radius: 41px;
                font-size: 23px;
                font-weight: bold;
            }

            QLabel#fullName {
                color: #F8FAFC;
                font-size: 22px;
                font-weight: bold;
            }

            QLabel#userRole {
                color: #C4B5FD;
                font-size: 13px;
            }

            QLabel#profileNote {
                color: #94A3B8;
                font-size: 12px;
            }

            QLabel#detailsTitle {
                color: #F8FAFC;
                font-size: 19px;
                font-weight: bold;
            }

            QLabel#detailsSubtitle {
                color: #94A3B8;
                font-size: 12px;
            }

            QFrame#infoField {
                background-color: #0F172A;
                border: 1px solid #303B53;
                border-radius: 9px;
            }

            QLabel#fieldLabel {
                color: #94A3B8;
                font-size: 12px;
            }

            QLabel#fieldValue {
                color: #F8FAFC;
                font-size: 14px;
                font-weight: bold;
            }

            QLabel#footerNote {
                color: #64748B;
                font-size: 12px;
            }

            QPushButton#backButton {
                background-color: #263248;
                color: #E2E8F0;
                border: 1px solid #35415A;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 16px;
            }

            QPushButton#backButton:hover {
                background-color: #35435D;
            }

            QPushButton:focus {
                outline: none;
            }
        """)

    # Tạo một trường thông tin gồm nhãn và giá trị
    def create_info_field(self, label_text, value_text):
        field = QFrame()
        field.setObjectName("infoField")
        field.setMinimumHeight(88)

        field_layout = QVBoxLayout()
        field_layout.setContentsMargins(14, 12, 14, 12)
        field_layout.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")

        value = QLabel(value_text)
        value.setObjectName("fieldValue")
        value.setWordWrap(True)

        field_layout.addWidget(label)
        field_layout.addWidget(value)
        field_layout.addStretch()

        field.setLayout(field_layout)

        return field


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = ProfileWindow()
    window.show()

    sys.exit(app.exec())
