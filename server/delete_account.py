from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt

class DeleteAccountDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Cấu hình hộp thoại
        self.setWindowTitle("Study Management - Xóa tài khoản")
        self.setFixedSize(400, 240)

        self.title = QLabel("XÓA TÀI KHOẢN")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2563EB;"
        )

        # Nd xác nhận
        self.message = QLabel(
            "Bạn có chắc chắc muốn xóa tài khoản\n"
            "và toàn bộ dữ liệu liên quan không?"
        )
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)

        self.warning = QLabel("Thao tác này không thể hoàn tác.")
        self.warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warning.setStyleSheet("color: #2563EB;")

        # Hai nút
        self.cancel_button = QPushButton("Hủy")
        self.delete_button = QPushButton("Xóa tài khoản")

        self.cancel_button.setMinimumHeight(40)
        self.delete_button.setMinimumHeight(40)

        # Sắp xếp hai nút theo chiều ngang
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.delete_button)

        # Sắp xếp toàn bộ hộp thoại theo chiều dọc
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        layout.addWidget(self.title)
        layout.addWidget(self.message)
        layout.addWidget(self.warning)
        layout.addSpacing(5)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }

            QLabel {
                color: #1F2937;
                font-size: 14px;
            }

            QPushButton {
                background-color: #F3F4F6;
                color: #1F2937;
                border: none;
                border-radius: 6px;
                padding: 9px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563EB;
                color: white;
            }

            QPushButton:last-child {
                background-color: #DC2626;
                color: white;
                font-weight: bold;
            }

            QPushButton:last-child:hover {
                background-color: #B91C1C;
            }
        """)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    dialog = DeleteAccountDialog()
    dialog.exec()