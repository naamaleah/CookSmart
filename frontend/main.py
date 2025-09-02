# file: frontend/main.py
import sys, os
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from views.main_view import MainWindow
from views.main_login_widget import LoginRegisterWidget 

# Simple app state manager
app_state = {"main": None, "login": None}

def on_login_success(token, username):
    app_state["main"] = MainWindow(
        token, logout_callback=show_login_window, username=username
    )
    app_state["main"].showMaximized()
    if app_state["login"]:
        app_state["login"].close()

def show_login_window():
    app_state["login"] = LoginRegisterWidget(on_login_success)
    app_state["login"].showMaximized()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Material theme
    apply_stylesheet(app, theme="light_amber.xml")

    # Load custom QSS (optional)
    style_path = os.path.join(os.path.dirname(__file__), "views", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, encoding="utf-8") as f:
            app.setStyleSheet(app.styleSheet() + f.read())

    # Start with login
    show_login_window()

    sys.exit(app.exec())
