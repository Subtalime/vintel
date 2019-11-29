from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QColorDialog
from PyQt5.QtCore import pyqtSignal

from vi.ui.Settings import Ui_Dialog
from vi.cache.cache import Cache


class SettingsDialog(QDialog, Ui_Dialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.cache = Cache()
        self.setupUi(self)
        self.color = None

        self.btnColor.clicked.connect(self.colorChooser)
        self.buttonBox.accepted.connect(self.saveSettings)
        self.buttonBox.rejected.connect(self.reject)
        self.txtKosInterval.setEnabled(False)

    def colorChooser(self):
        if self.color:
            backGroundColor = self.color.lstrip("#")
            lv = len(backGroundColor)
            bg = tuple(int(backGroundColor[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        else:
            bg = [0, 0, 0]
        color = QColorDialog.getColor(initial=QColor(bg[0], bg[1], bg[2]))
        if color.isValid():
            self.color = color.name()

    def saveSettings(self):
        self.settings_saved.emit()
        self.accept()
