from PyQt5.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QMessageBox,QTabWidget,QWidget,QFormLayout,QComboBox
from app.database.db import authenticate,create_user

class AuthWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taleem Dost AI — Login")
        self.setMinimumWidth(460)
        self.authenticated_user=None
        outer=QVBoxLayout(self)
        title=QLabel("🎓 Taleem Dost AI")
        title.setStyleSheet("font-size:21pt;font-weight:800;color:#5546D7;")
        subtitle=QLabel("Sign in or create a student account")
        subtitle.setStyleSheet("color:#69738C;")
        outer.addWidget(title); outer.addWidget(subtitle)
        tabs=QTabWidget(); outer.addWidget(tabs)

        login=QWidget(); form=QFormLayout(login)
        self.login_name=QLineEdit(); self.login_name.setPlaceholderText("Username or email")
        self.login_password=QLineEdit(); self.login_password.setEchoMode(QLineEdit.Password); self.login_password.setPlaceholderText("Password")
        form.addRow("Username / Email",self.login_name); form.addRow("Password",self.login_password)
        login_btn=QPushButton("Sign In"); login_btn.setObjectName("primary"); login_btn.clicked.connect(self.login)
        form.addRow(login_btn); tabs.addTab(login,"Login")

        register=QWidget(); reg=QFormLayout(register)
        self.full_name=QLineEdit(); self.new_username=QLineEdit(); self.new_email=QLineEdit()
        self.new_password=QLineEdit(); self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password=QLineEdit(); self.confirm_password.setEchoMode(QLineEdit.Password)
        reg.addRow("Full name",self.full_name); reg.addRow("Username",self.new_username)
        reg.addRow("Email",self.new_email); reg.addRow("Password",self.new_password)
        reg.addRow("Confirm password",self.confirm_password)
        hint=QLabel("Student accounts are created with the student role. Only an administrator can create teacher accounts.")
        hint.setWordWrap(True); reg.addRow(hint)
        reg_btn=QPushButton("Create Student Account"); reg_btn.setObjectName("primary"); reg_btn.clicked.connect(self.register)
        reg.addRow(reg_btn); tabs.addTab(register,"Student Registration")

    def login(self):
        user=authenticate(self.login_name.text(),self.login_password.text())
        if not user:
            QMessageBox.warning(self,"Login failed","Username/email or password is incorrect, or the account is disabled.")
            return
        self.authenticated_user=user
        self.accept()

    def register(self):
        if self.new_password.text()!=self.confirm_password.text():
            QMessageBox.warning(self,"Password mismatch","The passwords do not match."); return
        ok,msg=create_user(self.new_username.text(),self.full_name.text(),self.new_email.text(),self.new_password.text(),role="student")
        if ok:
            QMessageBox.information(self,"Registration complete",msg+" You can now sign in.")
            self.new_username.clear(); self.new_password.clear(); self.confirm_password.clear()
        else:
            QMessageBox.warning(self,"Registration failed",msg)
