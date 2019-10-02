import six
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QDialog, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, QObject
from vi.chatentrywidget import ChatEntryWidget
from vi import states
from vi.character import Characters

import vi.ui.SystemChat
import logging
class SystemChat(QtWidgets.QDialog, vi.ui.SystemChat.Ui_Dialog):
    SYSTEM = 0
    location_set = pyqtSignal(str, str)

    def __init__(self, parent: 'QObject', chatType, selector, chatEntries, knownPlayers: 'list'):
        QDialog.__init__(self, parent)
        # loadUi(resourcePath("vi/ui/SystemChat.ui"), self)
        if not isinstance(knownPlayers, list):
            logging.critical("SystemChat.init(knownPlayers) is not type of \"list\"")
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
