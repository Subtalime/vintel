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

import datetime
import math
import time
import logging
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.states import State
from vi.dotlan.soups import SoupSystem, SoupUse, SoupRect
from vi.dotlan.system import System
from vi.stopwatch.mystopwatch import ViStopwatch


class States:
    _state = {
        1: "ALARM",
        2: "CLEAR",
        3: "UNKNOWN",
        4: "REQUEST",
        5: "NO_CHANGE",
        6: "WAS_ALARMED",
        7: "LOCATION",
        8: "SOUND_TEST",
        9: "IGNORE",
    }
    _id = [1, 2, 3, 4, 5]
    _str = ["ALARM", "CLEAR", "UNKNOWN", "REQUEST"]

    def _get_state(self, state_num: int) -> str:
        if state_num in self._state.keys():
            return self._state[state_num]
        return self._state[3]

    @property
    def alarm(self):
        return self._get_state(1).replace("_", " ").lower()


class MySystem(System):
    messages = []
    stopwatch = ViStopwatch()
    status = State["UNKNOWN"]

    def __init__(self, system: SoupSystem, svg_soup: BeautifulSoup):
        self._system = system
        self._soup = svg_soup
        self.LOGGER = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """system name
        """
        return self._system.name

    @property
    def label(self) -> str:
        """name converted into a lable
        """
        return self.name.replace("-", "_").lower()

    @property
    def rect(self) -> SoupRect:
        """the Rectangle coordinates of the SVG symbol
        """
        return SoupRect(self._system.rectangles[0])

    def add_message(self, message):
        """received message.
        """
        self.messages.append(message)

    def del_message(self, message):
        """purge message.
        """
        if message in self.messages:
            self.messages.remove(message)
