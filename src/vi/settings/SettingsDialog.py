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

from PyQt5.QtWidgets import (
    QDialog,
    QMessageBox,
)
from PyQt5 import QtWidgets
from vi.settings import GeneralForm
from vi.sound import SoundForm
from vi.region import RegionsForm
from vi.chat import ChatroomsForm
from vi.color import ColorForm


from vi.ui.NewSettings import Ui_Dialog as New_Ui_Dialog


class SettingsDialog(QDialog, New_Ui_Dialog):
    def __init__(self, parent=None, activate_index=0):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle("Vintel Settings")
        self.applyButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply)
        self.applyButton.clicked.connect(self.apply_settings)
        self.applyButton.setEnabled(False)
        self.tabWidget.removeTab(self.tabWidget.indexOf(self.tab))
        self.tabWidget.removeTab(self.tabWidget.indexOf(self.tab_2))
        self.tab_general = GeneralForm.GeneralForm()
        self.tab_general.setObjectName("tab_general")
        self.tab_general.signal_content_changed.connect(self.apply_enable)
        self.tabWidget.addTab(self.tab_general, "General")
        self.tab_color_display = ColorForm.ColorForm()
        self.tab_color_display.setObjectName("tab_color")
        self.tab_color_display.signal_content_changed.connect(self.apply_enable)
        self.tabWidget.addTab(self.tab_color_display, "Color")
        self.tab_sound = SoundForm.SoundForm()
        self.tab_sound.setObjectName("tab_sound")
        self.tab_sound.signal_content_changed.connect(self.apply_enable)
        self.tabWidget.addTab(self.tab_sound, "Sound")
        self.tab_regions = RegionsForm.RegionsForm()
        self.tab_regions.setObjectName("tab_regions")
        self.tab_regions.signal_content_changed.connect(self.apply_enable)
        self.tabWidget.addTab(self.tab_regions, "Regions")
        self.tab_chatroom = ChatroomsForm.ChatroomsForm()
        self.tab_chatroom.setObjectName("tab_chatroom")
        self.tab_chatroom.signal_content_changed.connect(self.apply_enable)
        self.tabWidget.addTab(self.tab_chatroom, "Chat")
        self.buttonBox.accepted.connect(self.save_settings)
        self.buttonBox.rejected.connect(self.cancel_settings)
        self.tabWidget.setCurrentIndex(activate_index)

    def apply_enable(self):
        self.applyButton.setEnabled(True)

    def save_settings(self):
        self.save_all()
        self.accept()

    def save_all(self):
        if self.tab_general.data_changed:
            self.tab_general.save_data()
        if self.tab_color_display.data_changed:
            self.tab_color_display.save_data()
        if self.tab_sound.data_changed:
            self.tab_sound.save_data()
        if self.tab_regions.data_changed:
            self.tab_regions.save_data()
        if self.tab_chatroom.data_changed:
            self.tab_chatroom.save_data()

    def cancel_settings(self) -> None:
        if self.applyButton.isEnabled():
            res = QMessageBox.warning(
                self,
                "Cancel edit",
                "You have unsaved changes! Are you sure you wish to Cancel?",
                buttons=QMessageBox.Ok | QMessageBox.Cancel,
                defaultButton=QMessageBox.Cancel,
            )
            if res != QMessageBox.Ok:
                return
        self.reject()

    def apply_settings(self):
        self.save_all()
        self.applyButton.setEnabled(False)


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = SettingsDialog(None)
    d.show()
    r = d.exec_()
    # r = a.exec_()
    sys.exit(r)
