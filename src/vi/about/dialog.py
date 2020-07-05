#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QPixmap
from vi.ui.Info import Ui_Dialog
from vi.version import DISPLAY
from vi.resources import resourcePath


class AboutDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.versionLabel.setText(u"Version: {0}".format(DISPLAY))
        self.logoLabel.setPixmap(QPixmap(resourcePath("logo.png")))

        self.closeButton.setDefault(True)
        self.closeButton.clicked.connect(self.accept)

