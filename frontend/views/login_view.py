# frontend/views/login_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt


class LoginView(QWidget):
    """
    Login form view.
    Used inside LoginRegisterWidget and connected to its presenter.
    Provides input fields for username and password, plus login/register buttons.
    """

    def __init__(self):
        super().__init__()

        # --- Input fields ---
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(270)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(270)

        # --- Action buttons ---
        self.login_button = QPushButton("Login")
        self.login_button.setFixedWidth(270)

        self.register_button = QPushButton("Sign Up")
        self.register_button.setFixedWidth(270)

        # --- Error feedback label ---
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setVisible(False)

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        layout.addWidget(self.username_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.login_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.register_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.error_label, alignment=Qt.AlignCenter)
