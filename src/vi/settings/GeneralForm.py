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
import logging

from vi.color.helpers import color_dialog, string_to_color
from vi.settings.settings import GeneralSettings
from vi.settings.SettingsFormTemplate import SettingsFormTemplate
from vi.ui.GeneralForm import Ui_Form


class GeneralForm(SettingsFormTemplate, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.settings = GeneralSettings()
        self.colors = {
            "B": self.settings.background_color,
            "S": self.settings.color_ship,
            "C": self.settings.color_character,
            "Y": self.settings.color_system,
            "U": self.settings.color_url,
        }
        self.btnColor.clicked.connect(self.bkg_color)
        # populate the settings
        self.spinMessageExpiry.setMinimum(5)
        self.spinMessageExpiry.setMaximum(60)
        self.spinMessageExpiry.singleStep()
        self.spinMessageExpiry.setValue(self.settings.message_expiry / 60)
        self.spinMessageExpiry.valueChanged.connect(self.change_detected)
        self.checkShipNames.setChecked(self.settings.ship_parser)
        self.checkShipNames.stateChanged.connect(self.change_detected)
        self.checkScanCharacter.setChecked(self.settings.character_parser)
        self.checkScanCharacter.stateChanged.connect(self.change_detected)
        self.checkNotifyOwn.setChecked(self.settings.self_notify)
        self.checkNotifyOwn.stateChanged.connect(self.change_detected)
        self.checkPopupNotification.setChecked(self.settings.popup_notification)
        self.checkPopupNotification.stateChanged.connect(self.change_detected)
        self.spinDistance.setMinimum(0)
        self.spinDistance.setMaximum(6)
        self.spinDistance.singleStep()
        self.spinDistance.setValue(self.settings.alarm_distance)
        self.spinDistance.valueChanged.connect(self.change_detected)
        self.cmbLogLevel.addItem(logging.getLevelName(logging.DEBUG))
        self.cmbLogLevel.addItem(logging.getLevelName(logging.INFO))
        self.cmbLogLevel.addItem(logging.getLevelName(logging.WARN))
        self.cmbLogLevel.addItem(logging.getLevelName(logging.ERROR))
        self.cmbLogLevel.addItem(logging.getLevelName(logging.CRITICAL))
        self.cmbLogLevel.setCurrentText(logging.getLevelName(self.settings.log_level))
        self.cmbLogLevel.currentTextChanged.connect(self.change_detected)
        self.pbColorUrl.clicked.connect(self.url_color)
        self.pbColorShip.clicked.connect(self.ship_color)
        self.pbColorSystem.clicked.connect(self.system_color)
        self.pbColorCharacter.clicked.connect(self.character_color)

    def bkg_color(self):
        res = self.color_chooser(self.colors["B"])
        if res:
            self.colors["B"] = res

    def ship_color(self):
        res = self.color_chooser(self.colors["S"])
        if res:
            self.colors["S"] = res

    def character_color(self):
        res = self.color_chooser(self.colors["C"])
        if res:
            self.colors["C"] = res

    def url_color(self):
        res = self.color_chooser(self.colors["U"])
        if res:
            self.colors["U"] = res

    def system_color(self):
        res = self.color_chooser(self.colors["Y"])
        if res:
            self.colors["Y"] = res

    def color_chooser(self, the_color) -> str:
        color = string_to_color(the_color)
        color = color_dialog(color, self)
        if color.isValid():
            return color.name()
        return ""

    @property
    def data_changed(self) -> bool:
        if (
            self.checkNotifyOwn.isChecked() != self.settings.self_notify
            or int(self.spinDistance.value()) != int(self.settings.alarm_distance)
            or self.checkPopupNotification.isChecked()
            != self.settings.popup_notification
            or self.checkScanCharacter.isChecked() != self.settings.character_parser
            or self.checkShipNames.isChecked() != self.settings.ship_parser
            or int(self.spinMessageExpiry.value())
            != int(self.settings.message_expiry) / 60
            or self.cmbLogLevel.currentText()
            != logging.getLevelName(self.settings.log_level)
            or self.colors["B"] != self.settings.background_color
            or self.colors["C"] != self.settings.color_character
            or self.colors["S"] != self.settings.color_ship
            or self.colors["Y"] != self.settings.color_system
            or self.colors["U"] != self.settings.color_url
        ):
            return True
        return False

    def save_data(self):
        self.settings.self_notify = self.checkNotifyOwn.isChecked()
        self.settings.alarm_distance = self.spinDistance.value()
        self.settings.popup_notification = self.checkPopupNotification.isChecked()
        self.settings.character_parser = self.checkScanCharacter.isChecked()
        self.settings.ship_parser = self.checkShipNames.isChecked()
        self.settings.message_expiry = self.spinMessageExpiry.value() * 60
        if self.settings.log_level != logging.getLevelName(
            self.cmbLogLevel.currentText()
        ):
            self.settings.log_level = logging.getLevelName(
                self.cmbLogLevel.currentText()
            )
            # TODO: in log-file I always want debug... so get this right here!
            logging.getLogger().setLevel(self.settings.log_level)
        self.settings.background_color = self.colors["B"]
        self.settings.color_ship = self.colors["S"]
        self.settings.color_character = self.colors["C"]
        self.settings.color_system = self.colors["Y"]
        self.settings.color_url = self.colors["U"]

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
