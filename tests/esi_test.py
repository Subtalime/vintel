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


import os
import sys
from  vi.esi import *
from PyQt5.Qt import QApplication
import pytest
# @pytest.fixture
# def esi_cache():
#     return os.path.join(esi_cache_dir(), "esi-cache.sqlite3")
#
# @pytest.fixture
# def esi_cache_dir():
#     return os.path.join(os.path.dirname(__file__), "data")

@pytest.mark.parametrize("clientid", [("50de89684c374189a25ccf83aa1d928a")])
def test_esi_auth(esi_cache_dir, clientid):
    app = QApplication(sys.argv)

    EsiConfig.ESI_CLIENT_ID = clientid
    esi = EsiInterface(cache_dir=esi_cache_dir)

    assert esi, "ESI did not initialise"

#
# # from vi.esi.esithread import EsiThread, EsiInterface
# from PyQt5.Qt import QApplication
#
# LOGGER = logging.getLogger(__name__)
# if __name__ == "__main__":
#
#     app = QApplication(sys.argv)
#     # import requests
#
#     loghandler=None
#     logger_enabled=True
#
#     if logger_enabled:
#         log_format = '%(asctime)s %(levelname)-8s: %(name)s/%(funcName)s %(message)s'
#         log_format_con = '%(levelname)-8s: %(name)s/%(funcName)s %(message)s'
#         log_date = '%m/%d/%Y %I:%M:%S %p'
#         log_date = '%H:%M:%S'
#         logging.basicConfig(level=logging.DEBUG,
#                             format=log_format,
#                             datefmt=log_date)
#         console = logging.StreamHandler()
#         console.setLevel(level=logging.DEBUG)
#         console.setFormatter(logging.Formatter(log_format_con))
#         logging.getLogger().addHandler(console)
#
#     LOGGER.info("Instance of EsiInterface")
#     # LOGGER.info("Starting Thread")
#     # thread = EsiThread(cache_directory=".")
#     # thread.start()
#     # thread.requestInstance()
#     # LOGGER.info("Thread started")
#     # # LOGGER.info("Waiting 2 secs")
#     # time.sleep(2)
#     # LOGGER.info("Closing Thread")
#     # LOGGER.info("Requesting EsiInterface()")
#     esi = EsiInterface(cache_dir=".")
#     # thread.quit()
#     # LOGGER.info("Requesting EsiInterface()")
#     # es2 = EsiInterface()
#     LOGGER.info("Requesting Ship-List")
#     ships = esi.getShipList
#     LOGGER.info("Ship-List complete")
#
#     shipgroup = esi.getShipGroups()
#     for group in shipgroup['groups']:
#         shiptypes = esi.getShipGroupTypes(group)
#         for ship in shiptypes['types']:
#             shipitem = esi.getShip(ship)
#             ships.append(shipitem)
#
#     rr = dict(character_id=27378234)
#     oper = "get_characters_character_id"
#     resp = esi.esiApp.op[oper](**rr)
#
#
#
#     LOGGER.info("Requesting Systems")
#     res = esi.getSystemNames([95465449, 30000142])
#
#     chari = esi.getCharacterId("Tablot Manzari")
#     if chari:
#         print("getCharacterId: {}".format(chari))
#         charid = chari['character'][0]
#         chara = esi.getCharacter(charid)
#
#         character = chara  # Tablot Manzari
#         print("getCharacter: {}".format(character))
#
#         avatars = esi.getCharacterAvatar(charid)  # Tablot Manzari
#         print("getCharacterAvatar: {}".format(avatars))
#         imageurl = avatars["px64x64"]
#         corphist = esi.getCorporationHistory(charid)  # Bovril
#         print("getCorporationHistory: {}".format(corphist))
#         if isinstance(character, str):
#             esi.cache.delFromCache("get_characters_character_id_%s".format(charid))
#         else:
#             corp = esi.getCorporation(int(character['corporation_id']))  # Bovril
#             print("getCorporation: {}".format(corp))
#     li = ["B-7DFU", "Jita"]
#     ids = esi.getSystemIds(li)
#     if ids:
#         print("getSystemIds: {}".format(ids))
#         li = []
#         sys = ids['systems']
#         for a in sys:
#             li.append(a['id'])
#         names = esi.getSystemNames(li)
#         if names:
#             print("getSystemNames: {}".format(names))
#     jump_result = EsiInterface().getJumps()
#     if jump_result:
#         print("getJumps :{}".format(jump_result))
#         jumpData = {}
#         for data in jump_result:
#             jumpData[int(data['system_id'])] = int(data['ship_jumps'])
#     kill_result = EsiInterface().getKills()
#     if kill_result:
#         print("getKills :{}".format(kill_result))
#
