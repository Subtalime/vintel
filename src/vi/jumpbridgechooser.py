import six
import requests
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtCore import pyqtSignal
from vi.resources import resourcePath

import vi.ui.JumpbridgeChooser

class JumpbridgeChooser(QtWidgets.QDialog, vi.ui.JumpbridgeChooser.Ui_Dialog):
    set_jump_bridge_url = pyqtSignal(str)

    def __init__(self, parent, url):
        QDialog.__init__(self, parent)

        # loadUi(resourcePath("vi/ui/JumpbridgeChooser.ui"), self)
        self.setupUi(self)
        self.saveButton.clicked.connect(self.savePath)
        self.cancelButton.clicked.connect(self.accept)
        self.urlField.setText(url)
        # loading format explanation from textfile
        with open(resourcePath("docs/jumpbridgeformat.txt")) as f:
            self.formatInfoField.setPlainText(f.read())


    def savePath(self):
        try:
            url = six.text_type(self.urlField.text())
            if url != "":
                requests.get(url).text
            self.set_jump_bridge_url.emit(url)
            self.accept()
        except Exception as e:
            QMessageBox.critical(None, "Finding Jumpbridgedata failed", "Error: {0}".format(six.text_type(e)),
                                 QMessageBox.Ok)
