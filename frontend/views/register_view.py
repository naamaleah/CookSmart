# frontend/views/register_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt

class RegisterView(QWidget):
    """
    Simple registration form view (used inside LoginRegisterWidget).
    """
    def __init__(self):
        super().__init__()

        # Input fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(270)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email (e.g., name@example.com)")
        self.email_input.setFixedWidth(270)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        self.phone_input.setFixedWidth(270)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(270)

        # Buttons
        self.register_button = QPushButton("Register")
        self.register_button.setFixedWidth(270)

        self.back_button = QPushButton("Back")
        self.back_button.setFixedWidth(270)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setVisible(False)

        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        layout.setSpacing(10)

        layout.addWidget(self.username_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.email_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.phone_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.register_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.back_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.error_label, alignment=Qt.AlignCenter)
