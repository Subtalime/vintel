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
import logging
from vi.esi.esiinterface import EsiInterface
from vi.cache.cache import Cache

logger = logging.getLogger(__name__)
class EsiHelper:
    _ShipsUpper = {}
    _Ships = {}
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
            jumpData = {}
            jump_result = self.esi.getJumps()
            for data in jump_result:
                jumpData[int(data['system_id'])] = int(data['ship_jumps'])

            systemData = {}
            kill_result = self.esi.getKills()
            for data in kill_result:
                systemData[int(data['system_id'])] = {'ship': int(data['ship_kills']),
                                                      'faction': int(data['npc_kills']),
                                                      'pod': int(data['pod_kills'])}
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
    def ShipsUpper(self) -> dict:
        if len(self._ShipsUpper) == 0:
            for ship in self.esi.getShipList:
                self._ShipsUpper[str(ship['name']).upper()] = ship
        return self._ShipsUpper
    @property
    def Ships(self):
        if len(self._Ships) == 0:
            for ship in self.esi.getShipList:
                self._Ships[str(ship['name'])] = ship
        return self._Ships

    def getShipId(self, shipName: str) -> int:
        try:
            ship = self.ShipsUpper[shipName.upper()]
            return ship['type_id']
        except:
            logger.error("Unable to find Ship {}".format(shipName))
        return None
