# frontend/utils/message_box.py
from PySide6.QtWidgets import QMessageBox

class MessageBox:
    # Utility class that provides a unified and styled interface
    # for displaying different types of message dialogs in the UI.
    # Each method sets an objectName so that QSS can apply consistent theming.

    @staticmethod
    def show_info(parent, text: str):
        """
        Show an informational message dialog.
        Typically used for non-critical notifications (e.g., operation completed).
        """
        msg = QMessageBox(parent)
        msg.setObjectName("InfoBox")  # Enables QSS styling specifically for info dialogs
        msg.setWindowTitle("Info")    # Title displayed in the dialog's title bar
        msg.setText(text)             # Main body text shown to the user
        msg.setIcon(QMessageBox.Information)  # Standard "info" icon
        msg.exec()  # Execute modal dialog and block until closed

    @staticmethod
    def show_success(parent, text: str):
        """
        Show a success message dialog.
        Semantically similar to info, but styled differently (via QSS) to highlight success.
        """
        msg = QMessageBox(parent)
        msg.setObjectName("SuccessBox")   # Custom objectName for QSS theming
        msg.setWindowTitle("Success")     # Title indicates successful outcome
        msg.setText(text)
        msg.setIcon(QMessageBox.Information)  # Uses info icon; can be replaced with custom icon if needed
        msg.exec()

    @staticmethod
    def show_error(parent, text: str):
        """
        Show an error message dialog.
        Used for critical issues that require user awareness (e.g., failed operation).
        """
        msg = QMessageBox(parent)
        msg.setObjectName("ErrorBox")     # Custom objectName allows applying a red/error theme
        msg.setWindowTitle("Error")       # Title clearly indicates an error condition
        msg.setText(text)
        msg.setIcon(QMessageBox.Critical) # Standard "error" icon (red circle with X)
        msg.exec()

    @staticmethod
    def ask_confirm(parent, title: str, text: str) -> bool:
        """
        Show a confirmation dialog (Yes/No).
        Used when an operation requires explicit user confirmation.
        Returns True if 'Yes' is selected, False otherwise.
        """
        msg = QMessageBox(parent)
        msg.setObjectName("ConfirmBox")   # ObjectName allows unique QSS styling for confirmation dialogs
        msg.setWindowTitle(title)         # Caller can specify a custom title
        msg.setText(text)                 # Prompt text shown to the user
        msg.setIcon(QMessageBox.Question) # Question mark icon for clarity
        # Add Yes/No buttons to the dialog
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        # Default selection is 'No' to prevent accidental confirmations
        msg.setDefaultButton(QMessageBox.No)
        return msg.exec() == QMessageBox.Yes  # Returns True if user clicked Yes
