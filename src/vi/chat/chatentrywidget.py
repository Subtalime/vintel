#  Vintel - Visual Intel Chat Analyzer
#  Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#

import datetime
import logging
import sys
import webbrowser

import six
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget

import vi.ui.ChatEntry
from vi.chat.chatmessage import Message
from vi.resources import get_resource_path
from vi.settings.settings import GeneralSettings

LOGGER = logging.getLogger(__name__)


class ChatEntryWidgetInvalidItem(Exception):
    pass


class ChatEntryWidgetDeleted(Exception):
    pass


class ChatEntryWidget(QtWidgets.QWidget, vi.ui.ChatEntry.Ui_Form):
    """This is the actual Widget which displays the Chat-Message logged, complete with Links
    """
    _message = None
    TEXT_SIZE = 11
    SHOW_AVATAR = True
    mark_system = pyqtSignal(str)
    ship_detail = pyqtSignal(str)
    enemy_detail = pyqtSignal(str)

    # TODO: Hover over Ship-Bookmark gives Description?
    # Will not work on a Label... maybe use different type in the Widget...
    def __init__(self, message: Message):
        # QWidget.__init__(self)
        super(ChatEntryWidget, self).__init__()
        self.setupUi(self)
        self.LOGGER = logging.getLogger(__name__)
        self.QuestionMarkPixMap = QPixmap(get_resource_path("qmark.png")).scaledToHeight(32)
        self.avatarLabel.setPixmap(self.QuestionMarkPixMap)
        if not isinstance(message, Message):
            raise ChatEntryWidgetInvalidItem("not a message of type Message passed")
        self._message = message
        self.updateText()
        self.textLabel.linkActivated.connect(self.link_clicked)
        # if sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
        #     ChatEntryWidget.TEXT_SIZE = 8
        self.TEXT_SIZE = GeneralSettings().chat_entry_font_size
        self.changeFontSize(self.TEXT_SIZE)
        if not ChatEntryWidget.SHOW_AVATAR:
            self.avatarLabel.setVisible(False)

    @property
    def message(self) -> Message:
        return self._message

    def link_clicked(self, link):
        self.LOGGER.debug(f"Link {link} clicked")
        link = six.text_type(link)
        function, parameter = link.split("/", 1)
        self.LOGGER.debug(f"calling {function} with {parameter}")
        if function == "mark_system":
            self.mark_system.emit(parameter)
        elif function == "link":
            webbrowser.open(parameter)
        elif function == "show_enemy":
            self.enemy_detail.emit(parameter)
        elif function == "ship_name":
            self.ship_detail.emit(parameter)

    # doesn't work on a Label
    def updateTooltip(self, text: str):
        pos = text.find("title=")
        if pos != -1:
            title = ""
            links = BeautifulSoup(text, "html.parser").findAll("a")
            for link in links:
                thistitle = link.get("title")
                if thistitle:
                    title = title.join(thistitle + " ")
            if title:
                self.textLabel.setToolTip(title)

    def updateText(self):
        time = datetime.datetime.strftime(self.message.timestamp, "%H:%M:%S")
        display_text = "".join(str(item) for item in self.message.navigable_string.contents)
        text = u"<small>{time} - <b>{user}</b> - <i>{room}</i></small><br>{text}".format(
            user=self.message.user,
            room=self.message.room,
            time=time,
            text=display_text,
            # text=self.message.message,
        )
        try:
            self.textLabel.setText(text)
        except Exception:
            # widget no longer exists
            raise ChatEntryWidgetDeleted("QLabel has been deleted")
        # self.updateTooltip(self.message.message)

    def updateAvatar(self, avatarData):
        image = QImage.fromData(avatarData)
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return False
        scaledAvatar = pixmap.scaled(32, 32)
        self.avatarLabel.setPixmap(scaledAvatar)
        return True

    def changeFontSize(self, newSize):
        font = self.textLabel.font()
        font.setPointSize(newSize)
        ChatEntryWidget.TEXT_SIZE = newSize
        self.textLabel.setFont(font)
