#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
#

import six
import requests
import logging
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from vi.resources import resourcePath
import clipboard
import vi.ui.JumpbridgeChooser
from vi.jumpbridge import Import
from vi.settings.settings import RegionSettings


class JumpbridgeDialog(QtWidgets.QDialog, vi.ui.JumpbridgeChooser.Ui_Dialog):
    set_jump_bridge_url = pyqtSignal(str, str)
    LOGGER = logging.getLogger(__name__)

    def __init__(self, parent, url=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.saveButton.clicked.connect(self.savePath)
        self.cancelButton.clicked.connect(self.reject)
        self.clipboardButton.clicked.connect(self.saveClipboard)
        self.clipboardButton.setEnabled(True)
        url = RegionSettings().jump_bridge_url
        self.urlField.setText(url)
        # loading format explanation from textfile
        try:
            with open(resourcePath("docs/jumpbridgeformat.txt")) as f:
                self.formatInfoField.setPlainText(f.read())
        except FileNotFoundError:
            try:
                with open("docs/jumpbridgeformat.txt") as f:
                    self.formatInfoField.setPlainText(f.read())
            except FileNotFoundError:
                pass

    def savePath(self):
        try:
            url = six.text_type(self.urlField.text())
            if url != "" and url.startswith("http"):
                requests.get(url).text
            elif url != "":
                open(url, "r")
            self.accept()
            RegionSettings().jump_bridge_url = url
            self.set_jump_bridge_url.emit(url, None)
        except Exception as e:
            self.LOGGER.error("Finding Jumpbridgedata failed for \"%s\": %r" % (url, e, ))

    def accept(self) -> None:
        QDialog.accept(self)
        self.close()

    def saveClipboard(self):
            try:
                data = clipboard.paste()
                if data:
                    jb = Import.Import().readGarpaFile(clipboard=data)
                    if len(jb) > 0:
                        self.accept()
                        RegionSettings().jump_bridge_data = data
                        self.set_jump_bridge_url.emit(None, data)
                        self.close()
                    else:
                        QtWidgets.QMessageBox.warning(self, "Jumpbridgedata from Clipboard", "Invalid data found in Clipboard")
            except Exception as e:
                self.LOGGER.error("Error while using Clipboard-Jumpdata: %r", e)


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = JumpbridgeDialog(None)
    d.show()
    sys.exit(a.exec_())
