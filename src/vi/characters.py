from vi.cache.cache import Cache
import logging


class Characters:
    knownPlayers = dict()
    logPath = None
    cache = None

    def __init__(self, path_to_logs=None):
        self.logPath = path_to_logs
        self.cache = Cache()
        knownPlayerData = self.cache.getFromCache("known_players")
        if knownPlayerData:
            charsets = set(knownPlayerData.split(","))
            for char in charsets:
                try:
                    name, mon, location = char.split(".")
                    self.addCharacter(name, status=mon, location=location, store=False)
                except Exception as e:
                    logging.error("could not add player \"{}\"".format(name), e)

    def addCharacter(self, charname, status=True, location=None, store=True):
        self.knownPlayers[charname] = self.Character(charname, status, location)
        if store:
            self.storeData()

    def delCharacter(self, charname, store=True):
        if charname in self.knownPlayers:
            self.knownPlayers.pop(charname)
            if store:
                self.storeData()
        else:
            logging.warning("tried to remove character \"{}\" which does not exist".format(charname))


    def getCharacter(self, charname):
        if charname in self.knownPlayers:
            return self.knownPlayers.get(charname)
        return None

    def storeData(self):
        value = ",".join(str(x) for x in self.knownPlayers.values())
        self.cache.putIntoCache("known_players", value, 60 * 60 * 24 * 30)

    class Character:
        monitor = False
        charname = None
        location = None

        def __init__(self, charname, status=True, location=None):
            self.charname = charname
            self.monitor = bool(eval(str(status)))
            self.location = None if location == 'None' else location

        def update(self, monitor=None, location=None):
            if monitor:
                self.setMonitoring(monitor)
            if location:
                self.setLocation(location)
            return self

        def setMonitoring(self, enable):
            self.monitor = enable

        def setLocation(self, location):
            self.location = location

        def getLocations(self):
            return self.location

        def disable(self):
            self.setMonitoring(False)

        def enable(self):
            self.setMonitoring(True)

        def getName(self):
            return self.charname

        def getStatus(self):
            return self.monitor

        def getMonitoring(self):
            return self.getStatus()

        def __repr__(self):
            return "{}.{}.{}".format(self.charname, self.monitor, self.location)

# The main application
if __name__ == "__main__":
    chars = Characters()
    chars.addCharacter("test")
    chars.addCharacter("test", location="here")
    char = chars.getCharacter("test")
    char = chars.getCharacter("tt")
    chars.delCharacter("delw")
    chars.addCharacter("del")
