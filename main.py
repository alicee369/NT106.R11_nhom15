import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
)

from login import LoginWindow
from register import RegisterWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Study Management")
        self.setFixedSize(960, 600)

        # Tạo bộ chứa các trang
        self.stacked_widget = QStackedWidget()

        # Tạo form đăng nhập và đăng ký
        self.login_page = LoginWindow()
        self.register_page = RegisterWindow()

        # Đưa hai form vào QStackedWidget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.register_page)

        # Nhấn Đăng ký -> chuyển sang trang đăng ký
        self.login_page.register_requested.connect(
            lambda: self.stacked_widget.setCurrentIndex(1)
        )

        # Nhấn Đăng nhập -> quay lại trang đăng nhập
        self.register_page.login_requested.connect(
            lambda: self.stacked_widget.setCurrentIndex(0)
        )

        # Đặt QStackedWidget vào cửa sổ chính
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

