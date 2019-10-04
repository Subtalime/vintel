from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QUrl, QObject

class LoginDialog(QDialog):
    def __init__(self, parent: QObject=None, uri: QUrl):
        super.__init__(self, parent)


