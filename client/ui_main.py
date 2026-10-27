import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
)

from login import LoginWindow
from register import RegisterWindow
from profile import ProfileWindow  # Nhập ProfileWindow từ file profile.py[cite: 5]


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Study Management")
        self.setFixedSize(960, 600)

        # Tạo bộ chứa các trang
        self.stacked_widget = QStackedWidget()

        # Tạo form đăng nhập và đăng ký
        self.login_page = LoginWindow()  #[cite: 3]
        self.register_page = RegisterWindow()  #[cite: 6]

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

        # Lắng nghe sự kiện đăng nhập thành công từ LoginWindow[cite: 3]
        self.login_page.login_success.connect(self.on_login_success)

        # Đặt QStackedWidget vào cửa sổ chính
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

        self.setLayout(layout)

    def on_login_success(self, token: str):
        # Khởi tạo màn hình profile với token nhận được sau khi đăng nhập thành công[cite: 3, 5]
        self.profile_page = ProfileWindow(token)  #[cite: 5]
        
        # Xử lý sự kiện nếu tài khoản bị xóa thì quay về trang đăng nhập[cite: 5]
        self.profile_page.account_deleted.connect(self.on_account_deleted)

        self.stacked_widget.addWidget(self.profile_page)
        self.stacked_widget.setCurrentWidget(self.profile_page)
        self.setFixedSize(960, 640)  # Điều chỉnh kích thước cửa sổ phù hợp với ProfileWindow

    def on_account_deleted(self):
        # Quay về trang đăng nhập (index 0) khi tài khoản bị xóa
        self.stacked_widget.setCurrentIndex(0)
        self.setFixedSize(960, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())