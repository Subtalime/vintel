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
import logging
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, QObject
from vi.chatentrywidget import ChatEntryWidget
from vi import states
import vi.ui.SystemChat

LOGGER = logging.getLogger(__name__)


class SystemChat(QtWidgets.QDialog, vi.ui.SystemChat.Ui_Dialog):
    SYSTEM = 0
    location_set = pyqtSignal(str, str)

    def __init__(self, parent: 'QObject', chatType, selector, chatEntries, knownPlayers: 'list'):
        QDialog.__init__(self, parent)
        # loadUi(resourcePath("vi/ui/SystemChat.ui"), self)
        if not isinstance(knownPlayers, list):
            LOGGER.critical("SystemChat.init(knownPlayers) is not type of \"list\"")
            exit(-1)
        self.setupUi(self)
        self.parent = parent
        self.chatType = chatType
        self.selector = selector
        self.chatEntries = []
        for entry in chatEntries:
            self.addChatEntry(entry)
        titleName = ""
        if self.chatType == SystemChat.SYSTEM:
            titleName = self.selector.name
            self.system = selector
        for player in knownPlayers:
            self.playerNamesBox.addItem(player)
        self.setWindowTitle("Chat for {0}".format(titleName))
        # self.connect(self.closeButton, PYQT_SIGNAL("clicked()"), self.closeDialog)
        self.closeButton.clicked.connect(self.closeDialog)
        # self.connect(self.alarmButton, PYQT_SIGNAL("clicked()"), self.setSystemAlarm)
        self.alarmButton.clicked.connect(self.setSystemAlarm)
        # self.connect(self.clearButton, PYQT_SIGNAL("clicked()"), self.setSystemClear)
        self.clearButton.clicked.connect(self.setSystemClear)
        # self.connect(self.locationButton, PYQT_SIGNAL("clicked()"), self.locationSet)
        self.locationButton.clicked.connect(self.locationSet)

    def _addMessageToChat(self, message, avatarPixmap):
        scrollToBottom = False
        if (self.chat.verticalScrollBar().value() == self.chat.verticalScrollBar().maximum()):
            scrollToBottom = True
        entry = ChatEntryWidget(message)
        entry.avatarLabel.setPixmap(avatarPixmap)
        listWidgetItem = QListWidgetItem(self.chat)
        listWidgetItem.setSizeHint(entry.sizeHint())
        self.chat.addItem(listWidgetItem)
        self.chat.setItemWidget(listWidgetItem, entry)
        entry.mark_system.connect(self.parent.markSystemOnMap)
        self.chatEntries.append(entry)
        # self.connect(entry, PYQT_SIGNAL("mark_system"), self.parent.markSystemOnMap)
        if scrollToBottom:
            self.chat.scrollToBottom()

    def addChatEntry(self, entry):
        if self.chatType == SystemChat.SYSTEM:
            message = entry.message
            avatarPixmap = entry.avatarLabel.pixmap()
            if self.selector in message.systems:
                self._addMessageToChat(message, avatarPixmap)

    def locationSet(self):
        char = six.text_type(self.playerNamesBox.currentText())
        self.location_set.emit(char, self.system.name)
        # self.emit(PYQT_SIGNAL("location_set"), char, self.system.name)

    def newAvatarAvailable(self, charname, avatarData):
        for entry in self.chatEntries:
            if entry.message.user == charname:
                entry.updateAvatar(avatarData)

    def setSystemAlarm(self):
        self.system.setStatus(states.ALARM)
        self.parent.updateMapView()

    def setSystemClear(self):
        self.system.setStatus(states.CLEAR)
        self.parent.updateMapView()

    def closeDialog(self):
        self.accept()
