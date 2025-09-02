# frontend/presenters/register_presenter.py
from services.api import register_user, login_user

class RegisterPresenter:
    """
    Presenter for handling user registration.
    Responsible for:
    - Registering a new user.
    - Automatically logging them in upon success.
    - Handling navigation back to the login screen.
    - Displaying error messages in the view.
    """
    def __init__(self, view, on_login_success):
        self.view = view
        self.on_login_success = on_login_success

        # Navigation handler (overridden externally by LoginRegisterWidget)
        self.show_login = lambda: None

        # Connect buttons to handlers
        self.view.register_button.clicked.connect(self.on_register_clicked)
        self.view.back_button.clicked.connect(self.on_back_clicked)

    def on_register_clicked(self):
        """Handle register button click: validate input, attempt registration, and auto-login if successful."""
        username = self.view.username_input.text().strip()
        email = self.view.email_input.text().strip()
        phone = self.view.phone_input.text().strip()
        password = self.view.password_input.text().strip()

        if not all([username, email, phone, password]):
            self._show_error("Please fill in all fields")
            return

        success, message = register_user(username, password, email, phone)
        if success:
            # Auto-login after registration
            login_success, token = login_user(username, password)
            if login_success:
                self.on_login_success(token, username)
            else:
                self._show_error("Registration succeeded but login failed.")
        else:
            self._show_error(message)

    def on_back_clicked(self):
        """Handle back button click: navigate to login view."""
        self.show_login()

    def _show_error(self, message: str):
        """Helper to display error messages consistently."""
        if hasattr(self.view, "error_label"):
            self.view.error_label.setText(message)
            self.view.error_label.setVisible(True)
