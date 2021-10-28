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
from vi.chat.avatar import Avatar
from vi.resources import get_resource_path
from vi.settings.settings import GeneralSettings

LOGGER = logging.getLogger(__name__)


class ChatEntryWidgetInvalidItem(Exception):
    pass


class ChatEntryWidgetDeleted(Exception):
    pass


class AvatarUnknown(QPixmap):
    """Avatar image of unknown character
    """
    def __init__(self, image_or_path=None):
        if not image_or_path:
            image_or_path = get_resource_path("qmark.png")
        else:
            image = QImage.fromData(image_or_path)
            image_or_path = QPixmap.fromImage(image)

        super(AvatarUnknown, self).__init__(image_or_path)
        self.scaledToHeight(32)


class ChatEntryWidget(QtWidgets.QWidget, vi.ui.ChatEntry.Ui_Form):
    """This is the actual Widget which displays the Chat-Message logged, complete with Links
    """
    _message = None
    TEXT_SIZE = GeneralSettings().chat_entry_font_size
    SHOW_AVATAR = True
    mark_system = pyqtSignal(str)
    ship_detail = pyqtSignal(str)
    enemy_detail = pyqtSignal(str)

    def __init__(self, message: Message):
        super(ChatEntryWidget, self).__init__()
        self.setupUi(self)
        self.LOGGER = logging.getLogger(__name__)
        if not isinstance(message, Message):
            raise ChatEntryWidgetInvalidItem("not a message of type Message passed")
        self._message = message
        self.avatarLabel.setPixmap(Avatar(self.message.user))
        # self.avatarLabel.setPixmap(AvatarUnknown())
        self.update_text()
        self.textLabel.linkActivated.connect(self.link_clicked)
        self.change_font_size(self.TEXT_SIZE)
        if not ChatEntryWidget.SHOW_AVATAR:
            self.avatarLabel.setVisible(False)

    @property
    def message(self) -> Message:
        return self._message

    def link_clicked(self, link):
        """react on any hyperlink clicked within the displayed text
        """
        link = six.text_type(link)
        function, parameter = link.split("/", 1)
        self.LOGGER.debug(f"Link {link} has been clicked, calling {function} with {parameter}")
        if function == "mark_system":
            self.mark_system.emit(parameter)
        elif function == "link":
            webbrowser.open(parameter)
        elif function == "show_enemy":
            self.enemy_detail.emit(parameter)
        elif function == "ship_name":
            self.ship_detail.emit(parameter)

    def update_text(self):
        time = datetime.datetime.strftime(self.message.timestamp, "%H:%M:%S")
        display_text = "".join(str(item) for item in self.message.navigable_string.contents)
        text = u"<small>{time} - <b>{user}</b> - <i>{room}</i></small><br>{text}".format(
            user=self.message.user,
            room=self.message.room,
            time=time,
            text=display_text,
        )
        try:
            self.LOGGER.debug("About to update text with '%s'", text)
            self.textLabel.setText(text)
        except Exception:
            # widget no longer exists
            raise ChatEntryWidgetDeleted("Widget no longer exists")

    def update_avatar(self, avatar_data: bytes) -> bool:
        """update the Avatar image
        """
        image = QImage.fromData(avatar_data)
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return False
        scaled_avatar = pixmap.scaled(32, 32)
        self.avatarLabel.setPixmap(scaled_avatar)
        return True

    def change_font_size(self, new_size: int):
        font = self.textLabel.font()
        font.setPointSize(new_size)
        self.textLabel.setFont(font)
