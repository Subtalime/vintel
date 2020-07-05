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

from vi.cache.cache import Cache
import logging

LOGGER = logging.getLogger(__name__)


class Character:
    monitor = False
    charname = None
    location = None

    def __init__(self, charname: str, status: bool = True, location: str = None):
        self.charname = charname
        self.monitor = bool(eval(str(status)))
        self.location = None if location == "None" else location

    def update(self, monitor: bool = None, location: str = None):
        if monitor:
            self.setMonitoring(monitor)
        if location:
            self.setLocation(location)

    def setMonitoring(self, enable: bool):
        self.monitor = enable

    def setLocation(self, location: str):
        self.location = location

    def getLocation(self) -> str:
        return self.location

    def disable(self):
        self.setMonitoring(False)

    def enable(self):
        self.setMonitoring(True)

    def getName(self) -> str:
        return self.charname

    def getStatus(self) -> bool:
        return self.monitor

    def getMonitoring(self) -> bool:
        return self.getStatus()

    name = property(getName)

    def __repr__(self) -> str:
        return "{}.{}.{}".format(self.charname, self.monitor, self.location)


class Characters(dict):
    def __init__(self, path_to_logs: str = None):
        self._logPath = path_to_logs
        self._cache = Cache()
        self.pilots = []
        # initialize by Cache-Content
        self.load_data()

    def remove(self, *args):
        if len(args) > 0 and isinstance(args[0], Character):
            self.pop(args[0].getName())
        elif len(args) > 0:
            self.pop(args[0])

    def addName(
        self,
        charname: str,
        status: bool = True,
        location: str = None,
        store: bool = False,
    ) -> bool:
        if not isinstance(charname, str):
            LOGGER.critical('addName(charname) must be of type "str"')
            return False
        if charname not in self.keys():
            self[charname] = Character(charname, status, location)
            if store:
                self.store_data()
        else:
            return False
        return True

    def add_names(self, charnames: list) -> bool:
        if not isinstance(charnames, list):
            LOGGER.critical('addNames(charnames) must be of type "list"')
            return False
        new = False
        for charname in charnames:
            if self.addName(charname):
                new = True
        return new

    def add_character(self, character: Character, store: bool = False) -> bool:
        if not isinstance(character, Character):
            LOGGER.critical('addCharacter(character) needs to be type of "Character"')
            return False
        if character.getName() not in self.keys():
            self[character.getName()] = character
            if store:
                self.store_data()
        else:
            return False
        return True

    def pop(self, charname: str, store: bool = False):
        if not isinstance(charname, str):
            LOGGER.critical('pop(charname) is to be of type "str"')
        elif charname in self.keys():
            del self[charname]
            if store:
                self.store_data()
        else:
            LOGGER.warning(
                'tried to remove character "{}" which does not exist'.format(charname)
            )

    def get(self, charname: str) -> Character:
        if not isinstance(charname, str):
            LOGGER.critical('get(charname) is to be of type "str"')
        return self[charname]

    def get_names(self) -> list:
        chars = []
        for player in self.keys():
            chars.append(player)
        return chars

    def get_active_names(self) -> list:
        chars = []
        for player in self.keys():
            if self[player].getStatus():
                chars.append(player)
        return chars

    def load_data(self):
        known_player_data = self._cache.fetch("known_players")
        if known_player_data:
            charsets = set(known_player_data.split(","))
            for character in charsets:
                try:
                    arr = list(character.split("."))
                    self.add_character(Character(arr[0], arr[1], arr[2]))
                except Exception as e:
                    LOGGER.error('could not add player "%s": %r', character, e)
                    pass

    def store_data(self):
        value = ",".join(str(x) for x in self.values())
        self._cache.put("known_players", value, 60 * 60 * 24 * 30)

    def __repr__(self) -> str:
        return str(list(self.keys()))
