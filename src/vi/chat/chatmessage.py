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
from vi.resources import get_resource_path
from bs4 import Tag
import datetime
import time


class Message(object):
    """The Message-Parser
    stores the message, links, message poster, time
    """
    timestamp = None
    message = None
    user = None
    status = None
    _avatar = None
    # list of systems mentioned in the message
    systems = []
    # if you add the message to a widget, please add it to widgets
    widgets = []
    _navi_text = None

    def __init__(
        self,
        room: str,
        message: str,
        timestamp: datetime.datetime,
        user: str,
        plain_text: str = None,
        status: State = State["ALARM"],
        rtext: Tag = None,
        currsystems: list = None,
        upper_text: str = None,
        log_line: str = None,
        utc: datetime.datetime = None,
    ):
        self.room = room  # chatroom the message was posted
        self.message = message  # the messages text
        self.timestamp = timestamp  # time stamp of the massage
        self.user = user  # user who posted the message
        self.status = status  # status related to the message
        if rtext:
            self.navigable_string = rtext
        self.systems = (
            currsystems if currsystems is not None else []
        )  # list of systems mentioned in the message
        self._upper_text = (
            upper_text if upper_text else message.upper()
        )  # the text in UPPER CASE
        self._plain_text = (
            plain_text if plain_text else message
        )  # plain text of the message, as posted
        self.log_line = log_line
        self.utc_time = utc

    @property
    def timestamp_float(self) -> float:
        return time.mktime(self.timestamp.timetuple()) + self.timestamp.microsecond / 1e6

    @property
    def plain_text(self):
        return self._plain_text

    @property
    def upper_text(self):
        return self._upper_text

    @property
    def navigable_string(self) -> Tag:
        return self._navi_text

    @navigable_string.setter
    def navigable_string(self, value: Tag):
        if not isinstance(value, Tag):
            raise ValueError("Must be of type Tag")
        self._navi_text = value

    @property
    def avatar(self) -> bytes:
        if not self._avatar:
            with open(get_resource_path("qmark.png"), "rb") as f:
                self._avatar = f.read()
        return self._avatar

    def __key(self):
        return self.room, self.plain_text, self.timestamp, self.user

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __repr__(self):
        return "{} {}/'{}' {}: {}".format(
            self.timestamp, self.room, self.user, self.status.value, self.plain_text
        )

    def __hash__(self):
        return hash(self.__key())
