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

class JumpbridgeDialog(QtWidgets.QDialog, vi.ui.JumpbridgeChooser.Ui_Dialog):
    set_jump_bridge_url = pyqtSignal(str, str)

    def __init__(self, parent, url):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.saveButton.clicked.connect(self.savePath)
        self.cancelButton.clicked.connect(self.reject)
        self.clipboardButton.clicked.connect(self.saveClipboard)
        self.clipboardButton.setEnabled(True)
        self.urlField.setText(url)
        # loading format explanation from textfile
        with open(resourcePath("docs/jumpbridgeformat.txt")) as f:
            self.formatInfoField.setPlainText(f.read())

    def savePath(self):
        try:
            url = six.text_type(self.urlField.text())
            if url != "" and url.startswith("http"):
                requests.get(url).text
            elif url != "":
                open(url, "r")
            self.accept()
            self.set_jump_bridge_url.emit(url, None)
        except Exception as e:
            logging.error("Finding Jumpbridgedata failed for \"%s\": %r", url, e)

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
                        self.set_jump_bridge_url.emit(None, data)
                        self.close()
                    else:
                        QtWidgets.QMessageBox.warning(self, "Jumpbridgedata from Clipboard", "Invalid data found in Clipboard")
            except Exception as e:
                logging.error("Error while using Clipboard-Jumpdata: %r", e)