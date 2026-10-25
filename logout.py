
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)
from PySide6.QtCore import Qt


class LogoutDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Cấu hình hộp thoại
        self.setWindowTitle("Study Management - Đăng xuất")
        self.setFixedSize(420, 270)

        # Bố cục chính
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 25, 28, 25)
        layout.setSpacing(14)

        # Biểu tượng xác nhận
        self.icon_label = QLabel("↗")
        self.icon_label.setObjectName("iconLabel")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(48, 48)

        # Tiêu đề
        self.title = QLabel("Đăng xuất khỏi tài khoản?")
        self.title.setObjectName("dialogTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Nội dung xác nhận
        self.message = QLabel(
            "Bạn có chắc chắn muốn đăng xuất khỏi\n"
            "Study Management không?"
        )
        self.message.setObjectName("dialogMessage")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)

        # Hai nút
        self.cancel_button = QPushButton("Ở lại")
        self.logout_button = QPushButton("Đăng xuất")

        self.cancel_button.setMinimumHeight(40)
        self.logout_button.setMinimumHeight(40)

        self.cancel_button.setObjectName("cancelButton")
        self.logout_button.setObjectName("logoutButton")

        # Xếp hai nút theo chiều ngang
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.logout_button)

        # Xếp các thành phần theo chiều dọc
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)
        layout.addWidget(self.message)
        layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Định dạng giao diện
        self.setStyleSheet("""
            QDialog {
                background-color: #111827;
            }

            QLabel {
                background-color: transparent;
            }

            QLabel#iconLabel {
                background-color: #292044;
                color: #C4B5FD;
                font-size: 26px;
                font-weight: bold;
                border-radius: 24px;
            }

            QLabel#dialogTitle {
                color: #F8FAFC;
                font-size: 19px;
                font-weight: bold;
            }

            QLabel#dialogMessage {
                color: #94A3B8;
                font-size: 13px;
            }

            QPushButton {
                border: none;
                border-radius: 7px;
                padding: 9px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton#cancelButton {
                background-color: #263248;
                color: #E2E8F0;
            }

            QPushButton#cancelButton:hover {
                background-color: #35435D;
            }

            QPushButton#logoutButton {
                background-color: #7C3AED;
                color: white;
            }

            QPushButton#logoutButton:hover {
                background-color: #6D28D9;
            }

            QPushButton:focus {
                outline: none;
            }
        """)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    dialog = LogoutDialog()
    dialog.exec()
