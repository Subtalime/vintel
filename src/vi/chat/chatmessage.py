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
from vi import states
from bs4 import NavigableString
import datetime


class Message(object):
    def __init__(self, room: str, message: str, timestamp: datetime.datetime, user: str,
                 plainText: str = None, status: states = states.ALARM, rtext: NavigableString = None,
                 currsystems: list = None,
                 upperText: str = None):
        self.room = room  # chatroom the message was posted
        self.message = message  # the messages text
        self.timestamp = timestamp  # time stamp of the massage
        self.user = user  # user who posted the message
        self.systems = currsystems if currsystems is not None else [] # list of systems mentioned in the message
        self.status = status  # status related to the message
        self.upperText = upperText if upperText else message.upper()  # the text in UPPER CASE
        self.plainText = plainText if plainText else message  # plain text of the message, as posted
        self.rtext = rtext
        # if you add the message to a widget, please add it to widgets
        self.widgets = []

    def __key(self):
        return (self.room, self.plainText, self.timestamp, self.user)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __repr__(self):
        return "{} {}/'{}' {}: {}".format(self.timestamp, self.room, self.user, self.status.upper(), self.plainText)

    def __hash__(self):
        return hash(self.__key())
