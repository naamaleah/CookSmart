# File: frontend/views/main_login_widget.py
from PySide6.QtWidgets import (
    QVBoxLayout, QStackedLayout, QHBoxLayout,
    QFrame, QLabel
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from views.login_view import LoginView
from views.register_view import RegisterView
from presenters.login_presenter import LoginPresenter
from presenters.register_presenter import RegisterPresenter
from views.base_view import BaseView


class LoginRegisterWidget(BaseView):
    """
    Combined login/register widget with a stacked layout.
    Left side contains the logo and form, right side is left blank (background only).
    """

    def __init__(self, on_login_success):
        super().__init__()
        self.setWindowTitle("CookSmart - Login/Register")
        self.setMinimumSize(900, 600)
        self.on_login_success = on_login_success

        # --- Stacked forms (login + register) ---
        self.stack = QStackedLayout()
        self.login_view = LoginView()
        self.register_view = RegisterView()
        self.stack.addWidget(self.login_view)
        self.stack.addWidget(self.register_view)

        # Wrap stack vertically (center alignment)
        form_wrapper = QVBoxLayout()
        form_wrapper.addStretch(1)
        form_wrapper.addLayout(self.stack)
        form_wrapper.addStretch(1)

        form_container = QFrame()
        form_container.setObjectName("clear_frame")
        form_container.setLayout(form_wrapper)

        # Shift form horizontally to the right (inside left panel)
        form_shift_layout = QHBoxLayout()
        form_shift_layout.addStretch(7)
        form_shift_layout.addWidget(form_container)
        form_shift_layout.addStretch(3)

        # --- Logo ---
        self.logo_label = QLabel()
        self.logo_pixmap = QPixmap("frontend/images/clear_black_logo.png")
        self.logo_label.setAlignment(Qt.AlignLeft)

        # --- Left frame (logo + stacked form) ---
        self.left_frame = QFrame()
        self.left_frame.setObjectName("clear_frame")
        self.left_frame.setMinimumWidth(250)

        self.left_layout = QVBoxLayout(self.left_frame)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.addWidget(self.logo_label, alignment=Qt.AlignLeft )
        self.left_layout.addStretch(1)
        self.left_layout.addLayout(form_shift_layout)
        self.left_layout.addStretch(2)

        # --- Center layout (left frame + spacer) ---
        center_layout = QHBoxLayout()
        center_layout.addWidget(self.left_frame)
        center_layout.addStretch()

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        # --- Presenters ---
        self.login_presenter = LoginPresenter(self.login_view, on_login_success)
        self.register_presenter = RegisterPresenter(self.register_view, on_login_success)

        # Link navigation between forms
        self.login_presenter.show_register = lambda: self.stack.setCurrentWidget(self.register_view)
        self.register_presenter.show_login = lambda: self.stack.setCurrentWidget(self.login_view)

        # Initial logo size adjustment
        self.update_logo_size()

    # --- Resize handling ---
    def resizeEvent(self, event):
        """Ensure the logo is resized proportionally on window resize."""
        self.update_logo_size()
        super().resizeEvent(event)

    def update_logo_size(self):
        """Scale the logo width to ~2/3 of the window width, preserving aspect ratio."""
        if not self.logo_pixmap.isNull():
            window_width = self.width()
            desired_width = int(window_width * (2 / 3))
            scaled_pixmap = self.logo_pixmap.scaledToWidth(desired_width, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
