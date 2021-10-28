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
import logging
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal, QObject
from vi.chat.chatentrywidget import ChatEntryWidget
from vi.chat.chatlistwidget import ChatListWidget
from vi.states import State
from vi.dotlan.system import MySystem
from vi.character.Characters import Characters
import vi.ui.SystemChatDialog


class SystemChatDialog(QDialog, vi.ui.SystemChatDialog.Ui_Dialog):
    """Dialog to show the chat associated with the selected system"""

    location_set = pyqtSignal(str, str)
    window_close = pyqtSignal(MySystem)

    def __init__(
        self,
        parent: QObject,
        selected_system: MySystem,
        chat_entries: ChatListWidget,
        known_players: Characters,
    ):
        QDialog.__init__(self, parent)
        self.LOGGER = logging.getLogger(__name__)
        if not isinstance(known_players, Characters):
            self.LOGGER.critical(
                'SystemChat.init(knownPlayers) is not type of "Characters"'
            )
            exit(-1)
        self.setupUi(self)
        self.LOGGER.debug(f"System-Chat-Dialog opened for {selected_system.name}")
        self.parent = parent
        self.selected_system = selected_system
        self.chat_entries = chat_entries
        for entry in range(self.chat_entries.count()):
            self.add_chat_entry(self.chat_entries.get_widget(entry))
        # TODO: verify this!
        # only add characters which I "seem" to know, aren't here
        # characters = Characters()
        for player in known_players.keys():
            if known_players[player].getLocation() != self.selected_system.name:
                self.playerNamesBox.addItem(player)
        if len(self.playerNamesBox) == 0:
            self.locationButton.setEnabled(False)
        self.setWindowTitle(f"Chat for {self.selected_system.name}")
        self.closeButton.clicked.connect(self.closeDialog)
        self.alarmButton.clicked.connect(self._set_alarm)
        self.clearButton.clicked.connect(self._set_system_clear)
        self.locationButton.clicked.connect(self._set_location)
        self.parent.chat_message_added.connect(self.add_chat_entry)
        self.parent.avatar_loaded.connect(self.update_avatar)

    def add_chat_entry(self, entry: ChatEntryWidget):
        """add a widget to the List. This is also called from outside, if during the dialog
        being open, another message gets added
        """
        message = entry.message
        if self.selected_system in message.systems:
            self.chatList.add_message(message)

    def _set_location(self):
        character_name = six.text_type(self.playerNamesBox.currentText())
        # remove this character from the ComboBox
        index = self.playerNamesBox.findText(character_name)
        self.playerNamesBox.removeItem(index)
        self.location_set.emit(character_name, self.selected_system.name)

    def update_avatar(self, charname: str, avatar_data: bytes):
        for entry in range(self.chatList.count()):
            if self.chatList.get_message(entry).user == charname:
                the_chat = self.chatList.get_widget(entry)
                the_chat.update_avatar(avatar_data)

    def _set_alarm(self):
        self.selected_system.set_status(State["ALARM"])
        self.parent.updateMapView()

    def _set_system_clear(self):
        self.selected_system.set_status(State["CLEAR"])
        self.parent.updateMapView()

    def closeDialog(self):
        self.accept()
