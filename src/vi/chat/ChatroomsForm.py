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

from vi.settings.SettingsFormTemplate import SettingsFormTemplate
from vi.settings.settings import ChatroomSettings
from vi.ui.ChatroomsForm import Ui_Form


class ChatroomsForm(SettingsFormTemplate, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.room_names = ChatroomSettings().room_names
        self.txtChatrooms.setPlainText(self.room_names)
        self.txtChatrooms.textChanged.connect(self.change_detected)

    def get_data(self):
        text = self.txtChatrooms.toPlainText()
        rooms = [name.strip() for name in text.split(",")]
        return u",".join(rooms)

    def save_data(self):
        ChatroomSettings().room_names = self.get_data()

    @property
    def data_changed(self) -> bool:
        return self.get_data() != ChatroomSettings().room_names


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = ChatroomsForm()
    d.show()
    sys.exit(a.exec_())
