import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont
from app.database.db import initialize_database, admin_exists
from app.ui.auth_window import AuthWindow
from app.ui.main_window import MainWindow
from app.ui.setup_admin import FirstAdminDialog
from app.ui.styles import APP_STYLE

def main():
    initialize_database()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(APP_STYLE)

    if not admin_exists():
        setup = FirstAdminDialog()
        if setup.exec_() != FirstAdminDialog.Accepted:
            return

    auth = AuthWindow()
    if auth.exec_() == AuthWindow.Accepted and auth.authenticated_user:
        window = MainWindow(auth.authenticated_user)
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
