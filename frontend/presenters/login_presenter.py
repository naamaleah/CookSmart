# frontend/presenters/login_presenter.py
from services.api import login_user

class LoginPresenter:
    """
    Presenter for handling login logic.
    Responsible for:
    - Managing user authentication.
    - Handling button events for login and navigation to register view.
    - Displaying error messages in the view.
    """
    def __init__(self, view, on_login_success):
        self.view = view
        self.on_login_success = on_login_success

        # Navigation handler (overridden externally by LoginRegisterWidget)
        self.show_register = lambda: None

        # Connect buttons to handlers
        self.view.login_button.clicked.connect(self.on_login_clicked)
        self.view.register_button.clicked.connect(self.on_register_clicked)

    def on_login_clicked(self):
        """Handle login button click: validate input, attempt login, show errors if needed."""
        username = self.view.username_input.text().strip()
        password = self.view.password_input.text().strip()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        success, token_or_msg = login_user(username, password)

        if success:
            self.view.error_label.setVisible(False)
            self.on_login_success(token_or_msg, username)
        else:
            self._show_error(token_or_msg)

    def on_register_clicked(self):
        """Handle register button click: navigate to register view."""
        self.show_register()

    def _show_error(self, message: str):
        """Helper to display error messages consistently."""
        if hasattr(self.view, "error_label"):
            self.view.error_label.setText(message)
            self.view.error_label.setVisible(True)
