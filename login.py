from PySide6.QtWidgets import ( 
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal


class LoginWindow(QWidget):
    register_requested = Signal()

    def __init__(self):
        super().__init__()

        
        # Cấu hình cửa sổ
        self.setWindowTitle("Study Management - Đăng nhập")
        self.setMinimumSize(800, 520)

        # Bố cục chính: chia trái và phải
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =========================
        # VÙNG BÊN TRÁI: THƯƠNG HIỆU
        # =========================
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(18)

        self.brand_title = QLabel("◈ StudyManagement")
        self.brand_title.setObjectName("brandTitle")

        self.brand_heading = QLabel(
            "Learn smarter.\nGrow further."
        )
        self.brand_heading.setObjectName("brandHeading")

        self.brand_description = QLabel(
            "Không gian học tập cá nhân của bạn.\n"
            "Lập kế hoạch, quản lý và phát triển mỗi ngày."
        )
        self.brand_description.setObjectName("brandDescription")
        self.brand_description.setWordWrap(True)

        left_layout.addWidget(self.brand_title)
        left_layout.addStretch()
        left_layout.addWidget(self.brand_heading)
        left_layout.addWidget(self.brand_description)
        left_layout.addStretch()

        left_panel.setLayout(left_layout)

        # =========================
        # VÙNG BÊN PHẢI: FORM ĐĂNG NHẬP
        # =========================
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(12)

        self.title = QLabel("Chào mừng trở lại!")
        self.title.setObjectName("formTitle")

        self.subtitle = QLabel(
            "Đăng nhập để tiếp tục hành trình học tập."
        )
        self.subtitle.setObjectName("formSubtitle")
        self.subtitle.setWordWrap(True)

        self.username_label = QLabel("Tên đăng nhập")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nhập tên đăng nhập")

        self.password_label = QLabel("Mật khẩu")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.login_button = QPushButton("Đăng nhập")
        self.login_button.setMinimumHeight(44)
        self.login_button.clicked.connect(self.handle_login)

        self.register_text = QLabel(
            'Chưa có tài khoản? <a href="#">Đăng ký</a>'
        )
        self.register_text.setObjectName("registerText")
        self.register_text.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.register_text.setTextFormat(
            Qt.TextFormat.RichText
        )
        self.register_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.register_text.linkActivated.connect(
            lambda: self.register_requested.emit()
        )

        form_layout.addStretch()
        form_layout.addWidget(self.title)
        form_layout.addWidget(self.subtitle)
        form_layout.addSpacing(20)
        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(8)
        form_layout.addWidget(self.login_button)
        form_layout.addWidget(self.register_text)
        form_layout.addStretch()

        right_panel.setLayout(form_layout)

        # Ghép hai vùng vào bố cục chính
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

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

            QFrame#leftPanel {
                background-color: #111A30;
                border-right: 1px solid #27334D;
            }

            QFrame#rightPanel {
                background-color: #171D2E;
            }

            QLabel {
                background-color: transparent;
            }

            QLabel#brandTitle {
                color: #C4B5FD;
                font-size: 19px;
                font-weight: bold;
            }

            QLabel#brandHeading {
                color: #F8FAFC;
                font-size: 30px;
                font-weight: bold;
            }

            QLabel#brandDescription {
                color: #94A3B8;
                font-size: 13px;
            }

            QLabel#formTitle {
                color: #F8FAFC;
                font-size: 25px;
                font-weight: bold;
            }

            QLabel#formSubtitle {
                color: #94A3B8;
                font-size: 13px;
            }

            QLabel#registerText {
                color: #94A3B8;
            }

            QLabel#registerText a {
                color: #A78BFA;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #0B1020;
                color: #F8FAFC;
                border: 1px solid #35415A;
                border-radius: 7px;
                padding: 11px;
                selection-background-color: #7C3AED;
            }

            QLineEdit:focus {
                border: 1px solid #8B5CF6;
            }

            QPushButton {
                background-color: #7C3AED;
                color: white;
                border: none;
                border-radius: 7px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #6D28D9;
            }

            QPushButton:pressed {
                background-color: #5B21B6;
            }
        """)

    
    # Kiểm tra đầu vào phía giao diện
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self.show_message(
                "Thiếu thông tin",
                "Vui lòng nhập tên đăng nhập.",
                QMessageBox.Icon.Warning
            )
            return

        if not password:
            self.show_message(
                "Thiếu thông tin",
                "Vui lòng nhập mật khẩu.",
                QMessageBox.Icon.Warning
            )
            return

        self.show_message(
            "Thông báo",
            "Dữ liệu đã được nhập. Chức năng đăng nhập sẽ được kết nối sau.",
            QMessageBox.Icon.Information
        )

    # Hàm hiển thị hộp thoại
    def show_message(self, title, message, icon):
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }

            QLabel {
                background-color: transparent;
                color: #1F2937;
                font-size: 14px;
            }

            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)

        msg.exec()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

