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
from vi.states import State
from bs4 import NavigableString
import datetime
import time


class Message(object):
    def __init__(
        self,
        room: str,
        message: str,
        timestamp: datetime.datetime,
        user: str,
        plain_text: str = None,
        status: State = State["ALARM"],
        rtext: NavigableString = None,
        currsystems: list = None,
        upper_text: str = None,
        log_line: str = None,
        utc: datetime.datetime = None,
    ):
        self.room = room  # chatroom the message was posted
        self.message = message  # the messages text
        self.timestamp = timestamp  # time stamp of the massage
        self.timestamp_float = (
            time.mktime(timestamp.timetuple()) + timestamp.microsecond / 1e6
        )
        self.user = user  # user who posted the message
        self.status = status  # status related to the message
        self.rtext = rtext
        self.systems = (
            currsystems if currsystems is not None else []
        )  # list of systems mentioned in the message
        self.upper_text = (
            upper_text if upper_text else message.upper()
        )  # the text in UPPER CASE
        self.plain_text = (
            plain_text if plain_text else message
        )  # plain text of the message, as posted
        self.log_line = log_line
        self.utc_time = utc
        # if you add the message to a widget, please add it to widgets
        self.widgets = []

    @property
    def plainText(self):
        return self.plain_text

    @property
    def upperText(self):
        return self.upper_text

    @property
    def navigable_string(self) -> NavigableString:
        return self.rtext

    @navigable_string.setter
    def navigable_string(self, value: NavigableString):
        if not isinstance(value, NavigableString):
            raise ValueError("Must be of type NavigableString")
        self.rtext = value

    def __key(self):
        return (self.room, self.plainText, self.timestamp, self.user)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __repr__(self):
        return "{} {}/'{}' {}: {}".format(
            self.timestamp, self.room, self.user, self.status.value, self.plainText
        )

    def __hash__(self):
        return hash(self.__key())
