from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QColorDialog
from vi.ui.Settings import Ui_Dialog
from vi.cache.cache import Cache


class SettingsDialog(QDialog, Ui_Dialog):
    global app

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.cache = Cache()
        self.setupUi(self)
        self.btnColor.clicked.connect(self.colorChooser)


    def colorChooser(self):
        currcolor = self.cache.getFromCache("background_color", True)
        color = QColorDialog.getColor(initial=currcolor)
        if color.isValid():
            self.cache.putIntoCache("background_color")
            app.setStyleSheet("QWidget { background-color: %s; }" % color)


