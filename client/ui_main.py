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
        self.resize(960, 600)

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

        # Lắng nghe sự kiện đăng nhập thành công từ LoginWindow
        self.login_page.login_success.connect(self.on_login_success)

        # Đặt QStackedWidget vào cửa sổ chính
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

        self.setLayout(layout)

    def on_login_success(self, token: str):
        if hasattr(self, 'profile_page') and self.profile_page is not None:
            self.stacked_widget.removeWidget(self.profile_page)
            self.profile_page.deleteLater()

        # Khởi tạo màn hình profile với token nhận được sau khi đăng nhập thành công[cite: 3, 5]
        self.profile_page = ProfileWindow(token)  #[cite: 5]
        
        # Xử lý sự kiện nếu tài khoản bị xóa thì quay về trang đăng nhập[cite: 5]
        self.profile_page.account_deleted.connect(self.on_account_deleted)

        #Xử lý sk logout thành công 
        self.profile_page.logged_out.connect(self.on_logged_out)

        self.stacked_widget.addWidget(self.profile_page)
        self.stacked_widget.setCurrentWidget(self.profile_page)
        self.resize(960, 640)  
        self.center_window()

    def on_logged_out(self):
        # Xóa thông tin đăng nhập
        self.login_page.username_input.clear()
        self.login_page.password_input.clear()

        # Quay về login page
        self.stacked_widget.setCurrentIndex(0)
        self.resize(960, 600)
        self.center_window()

    def on_account_deleted(self):
        self.login_page.username_input.clear()
        self.login_page.password_input.clear()
        
        # Quay về login page khi delete account
        self.stacked_widget.setCurrentIndex(0)
        self.resize(960, 600)
        self.center_window()

    # Xử lý lỗi để tự động canh cửa sổ ra center màn hình
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())