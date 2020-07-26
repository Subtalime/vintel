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
from vi.jumpbridge.Import import Import
from vi.settings.settings import RegionSettings


class JumpbridgeDialog(QDialog, vi.ui.JumpbridgeChooser.Ui_Dialog):
    set_jump_bridge_url = pyqtSignal(str, str)

    def __init__(self, parent, url=None):
        super(self.__class__, self).__init__(parent)
        self.LOGGER = logging.getLogger(__name__)
        self.setupUi(self)
        self.saveButton.clicked.connect(self._save_path)
        self.cancelButton.clicked.connect(self.reject)
        self.clipboardButton.clicked.connect(self._save_clipboard)
        self.clipboardButton.setEnabled(True)
        url = RegionSettings().jump_bridge_url
        self.urlField.setText(url)
        # loading format explanation from textfile
        with open(resourcePath("docs/jumpbridgeformat.txt")) as f:
            self.formatInfoField.setPlainText(f.read())

    def _save_path(self):
        url = six.text_type(self.urlField.text())
        if len(Import().garpa_data(url)):
            RegionSettings().jump_bridge_url = url
            self.set_jump_bridge_url.emit(url, None)
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Jumpbridgedata from File/URL",
                "Invalid data found in File/URL",
            )

    def accept(self) -> None:
        super(self.__class__, self).accept()
        self.close()

    def _save_clipboard(self):
        try:
            data = clipboard.paste()
            if data:
                if len(Import().garpa_data(data)) > 0:
                    RegionSettings().jump_bridge_data = data
                    self.set_jump_bridge_url.emit(None, data)
                    self.accept()
                else:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Jumpbridgedata from Clipboard",
                        "Invalid data found in Clipboard",
                    )
        except Exception as e:
            self.LOGGER.error("Error while using Clipboard-Jumpdata: %r", e)


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = JumpbridgeDialog(None)
    d.show()
    sys.exit(a.exec_())
