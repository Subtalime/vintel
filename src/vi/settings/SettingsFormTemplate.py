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
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtCore import pyqtSignal


class SettingsFormTemplate(QWidget):
    signal_content_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

    def change_detected(self):
        self.signal_content_changed.emit()

    def save_data(self):
        raise NotImplementedError(
            "save_data method not implemented in %s" % (self.objectName())
        )

    @property
    def data_changed(self) -> bool:
        raise NotImplementedError("data_changed property not implemented")

    def is_saved(self):
        """here we would like to supply a signal, if the form has been saved.
        """
        pass

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stand-Alone Window will save if changed.
        """
        if self.data_changed:
            self.save_data()
