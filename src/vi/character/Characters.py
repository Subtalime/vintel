from vi.cache.cache import Cache
import logging

class Character:
    monitor = False
    charname = None
    location = None

    def __init__(self, charname: str, status: bool=True, location: str=None):
        self.charname = charname
        self.monitor = bool(eval(str(status)))
        self.location = None if location == 'None' else location

    def update(self, monitor: bool=None, location: str=None):
        if monitor:
            self.setMonitoring(monitor)
        if location:
            self.setLocation(location)

    def setMonitoring(self, enable: bool):
        self.monitor = enable

    def setLocation(self, location: str):
        self.location = location

    @property
    def getLocations(self) -> str:
        return self.location

    def disable(self):
        self.setMonitoring(False)

    def enable(self):
        self.setMonitoring(True)

    @property
    def getName(self) -> str:
        return self.charname

    @property
    def getStatus(self) -> bool:
        return self.monitor

    @property
    def getMonitoring(self) -> bool:
        return self.getStatus()

    def __repr__(self) -> str:
        return "{}.{}.{}".format(self.charname, self.monitor, self.location)

class Characters(dict):
    def __init__(self, path_to_logs: str=None):
        self._logPath = path_to_logs
        self._cache = Cache()
        # initialize by Cache-Content
        self.loadData()

    def remove(self, *args):
        if len(args) > 0 and isinstance(args[0], Character):
            self.pop(args[0].getName)
        elif len(args) > 0:
            self.pop(args[0])

    def addName(self, charname: str, status: bool=True, location: str=None, store: bool=False) -> bool:
        if not isinstance(charname, str):
            logging.critical("addName(charname) must be of type \"str\"")
            return False
        if charname not in self.keys():
            self[charname] = Character(charname, status, location)
            if store:
                self.storeData()
        else:
            return False
        return True

    def addNames(self, charnames: list) -> bool:
        if not isinstance(charnames, list):
            logging.critical("addNames(charnames) must be of type \"list\"")
            return False
        newAddition = False
        for charname in charnames:
            if self.addName(charname):
                newAddition = True
        return newAddition

    def addCharacter(self, character: Character, store: bool=False) -> bool:
        if not isinstance(character, Character):
            logging.critical("addCharacter(character) needs to be type of \"Character\"")
            return False
        if character.getName not in self.keys():
            self[character.getName] = character
            if store:
                self.storeData()
        else:
            return False
        return True

    def pop(self, charname: str, store: bool=False):
        if not isinstance(charname, str):
            logging.critical("pop(charname) is to be of type \"str\"")
        elif charname in self.keys():
            del self[charname]
            if store:
                self.storeData()
        else:
            logging.warning("tried to remove character \"{}\" which does not exist".format(charname))

    def get(self, charname: str) -> Character:
        if not isinstance(charname, str):
            logging.critical("get(charname) is to be of type \"str\"")
        elif charname in self.keys():
            return self[charname]
        return None

    def getNames(self) -> list:
        chars = []
        for player in self.keys():
            chars.append(player)
        return chars

    def getActiveNames(self) -> list:
        chars = []
        for player in self.keys():
            if self[player].getStatus:
                chars.append(player)
        return chars

    def loadData(self):
        knownPlayerData = self._cache.getFromCache("known_players")
        if knownPlayerData:
            charsets = set(knownPlayerData.split(","))
            for character in charsets:
                try:
                    arr = list(character.split("."))
                    self.addCharacter(Character(arr[0], arr[1], arr[2]))
                except Exception as e:
                    logging.error("could not add player \"%s\": %r", character, e)
                    pass

    def storeData(self):
        value = ",".join(str(x) for x in self.values())
        self._cache.putIntoCache("known_players", value, 60 * 60 * 24 * 30)

    def __repr__(self) -> str:
        return str(list(self.keys()))

