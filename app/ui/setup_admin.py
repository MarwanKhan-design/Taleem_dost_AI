from PyQt5.QtWidgets import QDialog,QVBoxLayout,QLabel,QLineEdit,QPushButton,QMessageBox
from app.database.db import create_user

class FirstAdminDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taleem Dost AI — Create Super Admin")
        self.setMinimumWidth(420)
        layout=QVBoxLayout(self)
        title=QLabel("Create your first administrator")
        title.setStyleSheet("font-size:16pt;font-weight:800;color:#101A35;")
        layout.addWidget(title)
        note=QLabel("This account will manage this local application. Use a strong, unique password.")
        note.setWordWrap(True); layout.addWidget(note)
        self.name=QLineEdit(); self.name.setPlaceholderText("Full name")
        self.username=QLineEdit(); self.username.setPlaceholderText("Admin username")
        self.email=QLineEdit(); self.email.setPlaceholderText("Admin email")
        self.password=QLineEdit(); self.password.setPlaceholderText("Password (10+ characters)"); self.password.setEchoMode(QLineEdit.Password)
        self.confirm=QLineEdit(); self.confirm.setPlaceholderText("Confirm password"); self.confirm.setEchoMode(QLineEdit.Password)
        for w in [self.name,self.username,self.email,self.password,self.confirm]: layout.addWidget(w)
        btn=QPushButton("Create Super Admin"); btn.setObjectName("primary"); btn.clicked.connect(self.create)
        layout.addWidget(btn)
    def create(self):
        if self.password.text()!=self.confirm.text():
            QMessageBox.warning(self,"Password mismatch","The passwords do not match."); return
        ok,msg=create_user(self.username.text(),self.name.text(),self.email.text(),self.password.text(),role="admin")
        if ok:
            QMessageBox.information(self,"Admin created",msg+" You can now log in.")
            self.accept()
        else:
            QMessageBox.warning(self,"Could not create admin",msg)
