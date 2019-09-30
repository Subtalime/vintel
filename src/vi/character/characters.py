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
        if charname not in self.knownPlayers:
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

    def getCharacterNames(self):
        chars = []
        for player in self.knownPlayers.keys():
            chars.append(player)
        return chars

    def storeData(self):
        value = ",".join(str(x) for x in self.knownPlayers.values())
        self.cache.putIntoCache("known_players", value, 60 * 60 * 24 * 30)


