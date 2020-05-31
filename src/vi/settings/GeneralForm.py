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
from PyQt5.QtGui import QIntValidator
from vi.color.helpers import color_dialog, string_to_color
from vi.ui.GeneralForm import Ui_Form
from vi.settings.SettingsFormTemplate import SettingsFormTemplate
from vi.settings.settings import GeneralSettings


class GeneralForm(SettingsFormTemplate, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.color = None
        self.settings = GeneralSettings()
        self.txtKosInterval.setEnabled(False)
        self.btnColor.clicked.connect(self.color_chooser)
        # populate the settings
        self.txtKosInterval.setText(str(int(self.settings.clipboard_check_interval / 1000)))
        self.txtKosInterval.setValidator(QIntValidator())
        self.txtKosInterval.textChanged.connect(self.change_detected)
        self.txtMessageExpiry.setText(str(self.settings.message_expiry))
        self.txtMessageExpiry.setValidator(QIntValidator())
        self.txtMessageExpiry.textChanged.connect(self.change_detected)
        self.checkShipNames.setChecked(self.settings.ship_parser)
        self.checkShipNames.stateChanged.connect(self.change_detected)
        self.checkScanCharacter.setChecked(self.settings.character_parser)
        self.checkScanCharacter.stateChanged.connect(self.change_detected)
        self.checkNotifyOwn.setChecked(self.settings.self_notify)
        self.checkNotifyOwn.stateChanged.connect(self.change_detected)
        self.checkPopupNotification.setChecked(self.settings.popup_notification)
        self.checkPopupNotification.stateChanged.connect(self.change_detected)
        self.txtJumpDistance.setText(str(self.settings.alarm_distance))
        self.txtJumpDistance.setValidator(QIntValidator())
        self.txtJumpDistance.textChanged.connect(self.change_detected)
        self.color = self.settings.background_color

    def color_chooser(self):
        color = string_to_color(self.color)
        color = color_dialog(color)
        if color.isValid():
            self.color = color.name()
            self.change_detected()

    @property
    def data_changed(self) -> bool:
        if self.checkNotifyOwn.isChecked() != self.settings.self_notify or \
                self.txtJumpDistance.text() != str(self.settings.alarm_distance) or \
                self.checkPopupNotification.isChecked() != self.settings.popup_notification or \
                self.checkScanCharacter.isChecked() != self.settings.character_parser or \
                self.checkShipNames.isChecked() != self.settings.ship_parser or \
                self.txtMessageExpiry.text() != str(self.settings.message_expiry) or \
                self.txtKosInterval.text() != str(int(self.settings.clipboard_check_interval / 1000)) or \
                self.color != self.settings.background_color:
            return True
        return False

    def save_data(self):
        self.settings.self_notify = self.checkNotifyOwn.isChecked()
        self.settings.alarm_distance = self.txtJumpDistance.text()
        self.settings.popup_notification = self.checkPopupNotification.isChecked()
        self.settings.character_parser = self.checkScanCharacter.isChecked()
        self.settings.ship_parser = self.checkShipNames.isChecked()
        self.settings.message_expiry = self.txtMessageExpiry.text()
        self.settings.clipboard_check_interval = int(self.txtKosInterval.text()) * 1000
        self.settings.background_color = self.color

    def closeEvent(self, a0) -> None:
        if self.data_changed:
            self.save_data()


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = GeneralForm()
    d.show()
    sys.exit(a.exec_())

