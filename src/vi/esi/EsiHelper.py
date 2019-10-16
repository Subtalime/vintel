from typing import Optional, Any

import requests, datetime, json, logging
from vi.esi.EsiInterface import EsiInterface
from vi.cache.cache import Cache

class EsiHelper:
    _ShipNames = []

    def __init__(self):
        self.esi = EsiInterface()
        self.cache = Cache()

    def getAvatarByName(self, characterName: str) -> str:
        resp = self.esi.getCharacterAvatarByName(characterName)
        if resp:
            imageurl = resp.data["px64x64"]
            avatar = requests.get(imageurl).content
            return avatar
        return None

    def getAvatarById(self, characterId: int) -> str:
        resp = self.esi.getCharacterAvatar(characterId)
        if resp:
            imageurl = resp.data["px64x64"]
            avatar = requests.get(imageurl).content
            return avatar
        return None

    def checkPlayerName(self, characterName: str) -> bool:
        resp = self.esi.getCharacterId(characterName, True)
        if resp and len(resp.data) > 0:
            for charid in resp.data["character"]:
                character = self.esi.getCharacter(charid)
                if character and character.data["name"] == characterName:
                    return True
        return False

    def getSystemStatistics(self) -> dict:
        try:
            cacheKey = "_".join(("esihelper", "jumpstatistics"))
            jumpData = self.cache.getFromCache(cacheKey)
            if not jumpData:
                jumpData = {}
                jump_result = self.esi.getJumps()
                for data in jump_result.data:
                    jumpData[int(data['system_id'])] = int(data['ship_jumps'])
                if len(jumpData):
                    expire_date = jump_result.header.get('Expires')[0]
                    cacheUntil = datetime.datetime.strptime(expire_date, "%a, %d %b %Y %H:%M:%S %Z")
                    diff = cacheUntil - self.esiClient.currentEveTime()
                    self.cache.putIntoCache(cacheKey, json.dumps(jumpData), diff.seconds)
            else:
                jumpData = json.loads(jumpData)

            cacheKey = "_".join(("esihelper", "systemstatistic"))
            systemData = self.cache.getFromCache(cacheKey)
            if not systemData:
                systemData = {}
                kill_result = self.esi.getKills()
                for data in kill_result.data:
                    systemData[int(data['system_id'])] = {'ship': int(data['ship_kills']),
                                                          'faction': int(data['npc_kills']),
                                                          'pod': int(data['pod_kills'])}
                if len(systemData):
                    expire_date = kill_result.header.get('Expires')[0]
                    cacheUntil = datetime.datetime.strptime(expire_date, "%a, %d %b %Y %H:%M:%S %Z")
                    diff = cacheUntil - self.esi.currentEveTime()
                    self.cache.putIntoCache(cacheKey, json.dumps(systemData), diff.seconds)
            else:
                systemData = json.loads(systemData)
        except Exception as e:
            logging.error("Exception during getSystemStatistics: : %s", e)

        data = {}
        # We collected all data (or loaded them from cache) - now zip it together
        for i, v in jumpData.items():
            i = int(i)
            if i not in data:
                data[i] = {"shipkills": 0, "factionkills": 0, "podkills": 0}
            data[i]["jumps"] = v
        for i, v in systemData.items():
            i = int(i)
            if i not in data:
                data[i] = {"jumps": 0}
            data[i]["shipkills"] = v["ship"] if "ship" in v else 0
            data[i]["factionkills"] = v["faction"] if "faction" in v else 0
            data[i]["podkills"] = v["pod"] if "pod" in v else 0
        return data

    @property
    def ShipNames(self) -> list:
        if len(self._ShipNames) == 0:
            ships = self.esi.getShipList
            for ship in ships:
                self._ShipNames.append(str(ship['name']).upper())
        return self._ShipNames

