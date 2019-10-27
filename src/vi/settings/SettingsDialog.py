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
        self.btnColor.clicked.connect(self.colorChooser)
        self.buttonBox.accepted.connect(self.saveSettings)
        self.buttonBox.rejected.connect(self.accept)
        self.txtClipboardCheckInterval.setText(str(int(self.cache.getFromCache("clipboard_check_interval", True)) / 1000))
        self.txtMapExpiry.setText(str(int(self.cache.getFromCache("map_update_interval", True)) / 1000))
        self.txtMessageExpiry.setText(str(int(self.cache.getFromCache("message_expiry", True)) / 60))

    def colorChooser(self):
        currcolor = self.cache.getFromCache("background_color", True)
        if currcolor:
            backGroundColor = currcolor.lstrip("#")
            lv = len(backGroundColor)
            bg = tuple(int(backGroundColor[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        else:
            bg = [0, 0, 0]
        color = QColorDialog.getColor(initial=QColor(bg[0], bg[1], bg[2]))
        if color.isValid():
            self.cache.putIntoCache("background_color", color.name())

    # TODO: save the settings and create a Trigger for listeners
    def saveSettings(self):
        self.cache.putIntoCache("clipboard_check_interval", str(int(self.txtClipboardCheckInterval.toPlainText()) * 1000))
        self.cache.putIntoCache("map_update_interval", str(int(self.txtMapExpiry.toPlainText()) * 1000))
        self.cache.putIntoCache("message_expiry", str(int(self.txtMessageExpiry.toPlainText()) * 60))
        self.settings_saved.emit()
        self.accept()
