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
import time

from PyQt5.QtWidgets import QListWidget, QWidget, QAbstractItemView, QListView, QListWidgetItem
from PyQt5.QtCore import Qt

from vi.esi import EsiInterface
from vi.settings.settings import GeneralSettings
from vi.chat.chatmessage import Message
from vi.chat.chatentrywidget import ChatEntryWidget


class ChatListWidget(QListWidget):
    """a list of chat entries represented by ChatEntryWidgets
    """
    def __init__(self, parent: QWidget):
        super(ChatListWidget, self).__init__(parent)
        self.LOGGER = logging.getLogger(__name__)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setResizeMode(QListView.Adjust)

    def update_font_size(self, size: int):
        self.LOGGER.debug(f"change font size to {size}")
        for item in range(self.count()):
            self.itemWidget(self.item(item)).changeFontSize(size)

    def add_message(self, message: Message) -> ChatEntryWidget:
        self.LOGGER.debug(f"adding {message} to list")
        scroll_to_bottom = False
        if (
            self.verticalScrollBar().value()
            == self.verticalScrollBar().maximum()
        ):
            scroll_to_bottom = True
        chat_entry_widget = ChatEntryWidget(message)
        list_widget_item = QListWidgetItem(self)
        list_widget_item.setSizeHint(chat_entry_widget.sizeHint())

        self.addItem(list_widget_item)
        self.setItemWidget(list_widget_item, chat_entry_widget)

        if scroll_to_bottom:
            self.scrollToBottom()
        self.LOGGER.debug(f"finished adding {message} to list")
        return chat_entry_widget

    def get_message(self, index: int = 0) -> Message:
        """retrieve the Message in the Widget-List
        :param index: offset within the Widget-List
        :type index: int
        """
        self.LOGGER.debug(f"retrieve message {index}")
        return self.itemWidget(self.item(index)).message

    def get_widget(self, index: int = 0) -> ChatEntryWidget:
        self.LOGGER.debug(f"retrieve widget {index}")
        the_widget = self.itemWidget(self.item(index))
        # this is actually returning a ChatEntryWidget... PyCharm doesn't think so
        return the_widget

    def get_message_list(self) -> list:
        """return a list of all Messages stored in the Chat-List
        """
        messages = []
        for msg in range(self.count()):
            messages.append(self.get_message(msg))
        return messages

    def prune_messages(self):
        """remove items, which have expired based on settings
        """
        cleared_messages = False
        # how long to retain messages in the list
        message_expiry = GeneralSettings().message_expiry
        eve_now = time.mktime(EsiInterface().currentEveTime().timetuple())
        self.LOGGER.debug(f"starting prune in list of {self.count()} messages in list")
        # go through the list, starting at the top
        for row in range(self.count()):
            # top message in the list
            message = self.get_message()
            diff = eve_now - time.mktime(message.utc_time.timetuple())
            try:
                # check if message is older than the retaining time
                if diff > message_expiry:
                    # remove the widget from the list within the message
                    # TODO: not sure why we have this in the message.widget or even maintain this list...
                    try:
                        message.widgets.remove(self.get_widget())
                    except ValueError:
                        self.LOGGER.error(f"Widget {message} was not logged in message.widget list")
                        pass
                    self.LOGGER.debug(f"remove {message} from message list")
                    self.takeItem(0)
                    cleared_messages = True
            except Exception as e:
                self.LOGGER.error(
                    "Age is {diff} and expiry is {exp}: %r".format(
                        diff=diff, exp=self.message_expiry
                    ),
                    e,
                )
        self.LOGGER.debug(f"finished prune in list with {self.count()} messages in list remaining")
        if cleared_messages:
            # after delete, make sure we are showing the latest message in the UI
            self.scrollToBottom()
