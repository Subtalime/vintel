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

import requests
import json
from vi.esi.esiinterface import EsiInterface
from vi.cache.cache import Cache

class EsiHelper:
    _ShipNames = []
    _ShipNamesUpper = []

    def __init__(self):
        self.esi = EsiInterface()
        self.cache = Cache()

    def getAvatarByName(self, characterName: str) -> str:
        resp = self.esi.getCharacterAvatarByName(characterName)
        if resp:
            imageurl = resp["px64x64"]
            avatar = requests.get(imageurl).content
            return avatar
        return None

    def getAvatarById(self, characterId: int) -> str:
        resp = self.esi.getCharacterAvatar(characterId)
        if resp:
            imageurl = resp["px64x64"]
            avatar = requests.get(imageurl).content
            return avatar
        return None

    def checkPlayerName(self, characterName: str) -> bool:
        resp = self.esi.getCharacterId(characterName, True)
        if resp:
            for charid in resp["character"]:
                character = self.esi.getCharacter(charid)
                if character and character.get("name") == characterName:
                    return True
        return False

    def getSystemStatistics(self) -> dict:
        try:
            cacheKey = "_".join(("esihelper", "jumpstatistics"))
            jumpData = self.cache.getFromCache(cacheKey)
            if not jumpData:
                jumpData = {}
                jump_result, expiry = self.esi.getJumps()
                for data in jump_result:
                    jumpData[int(data['system_id'])] = int(data['ship_jumps'])
                if len(jumpData):
                    self.cache.putIntoCache(cacheKey, json.dumps(jumpData), expiry.seconds)
            else:
                jumpData = json.loads(jumpData)

            cacheKey = "_".join(("esihelper", "systemstatistic"))
            systemData = self.cache.getFromCache(cacheKey)
            if not systemData:
                systemData = {}
                kill_result, expiry = self.esi.getKills()
                for data in kill_result:
                    systemData[int(data['system_id'])] = {'ship': int(data['ship_kills']),
                                                          'faction': int(data['npc_kills']),
                                                          'pod': int(data['pod_kills'])}
                if len(systemData):
                    self.cache.putIntoCache(cacheKey, json.dumps(systemData), expiry.seconds)
            else:
                systemData = json.loads(systemData)
        except Exception:
            raise

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
            for ship in self.esi.getShipList:
                self._ShipNames.append(str(ship['name']))
        return self._ShipNames
    @property
    def ShipNamesUpper(self) -> list:
        if len(self._ShipNamesUpper) == 0:
            for ship in self.esi.getShipList:
                self._ShipNamesUpper.append(str(ship['name']).upper())
        return self._ShipNamesUpper

    def getShipId(self, shipName: str) -> int:
        for ship in self.esi.getShipList:
            if ship["name"] == shipName:
                return ship["id"]
        return None

