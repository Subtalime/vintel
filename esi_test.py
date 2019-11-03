#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#  #
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#  #
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#  #
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#  #
#  #
#
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
import time, logging, sys
from vi.esi.esiinterface import EsiInterface, EsiThread
from PyQt5.Qt import QApplication

if __name__ == "__main__":
    def _cacheVar(function: str, *argv):
        args = argv.__repr__()
        l = []
        for a in argv:
            l.append(str(a))
        return "_".join(("esicache", function)) + "_".join((str(argv.__repr__())))

    app = QApplication(sys.argv)
    # root logger set
    logging.getLogger().setLevel(logging.DEBUG)
    es2 = EsiInterface(cacheDir=".")

    a = _cacheVar("test", 1, "me")

    import requests, datetime

    log_format = '%(asctime)s %(levelname)-8s: %(name)s/%(funcName)s %(message)s'
    log_format_con = '%(levelname)-8s: %(name)s/%(funcName)s %(message)s'
    log_date = '%m/%d/%Y %I:%M:%S %p'
    log_date = '%H:%M:%S'
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format,
                        datefmt=log_date)
    # console = logging.StreamHandler()
    # console.setLevel(level=logging.DEBUG)
    # console.setFormatter(logging.Formatter(log_format_con))
    #
    # logger = logging.getLogger(__name__)
    # logger.addHandler(console)
    # logging.getLogger().setLevel(logging.DEBUG)

    thread = EsiThread()
    thread.start(1)
    thread.requestInstance()
    time.sleep(2)
    esi = EsiInterface()
    thread.quit()
    es2 = EsiInterface()
    ships = esi.getShipList

    shipgroup = esi.getShipGroups()
    for group in shipgroup['groups']:
        shiptypes = esi.getShipGroupTypes(group)
        for ship in shiptypes['types']:
            shipitem = esi.getShip(ship)
            ships.append(shipitem)

    res = esi.getSystemNames([95465449, 30000142])

    chari = esi.getCharacterId("Tablot Manzari")
    if chari:
        print("getCharacterId: {}".format(chari))
        charid = chari['character'][0]
        chara = esi.getCharacter(charid)

        character = chara.data  # Tablot Manzari
        print("getCharacter: {}".format(character))

        avatars = esi.getCharacterAvatar(charid)  # Tablot Manzari
        print("getCharacterAvatar: {}".format(avatars))
        imageurl = avatars["px64x64"]
        avatar = requests.get(imageurl).content
        corphist = esi.getCorporationHistory(charid)  # Bovril
        print("getCorporationHistory: {}".format(corphist))
        corp = esi.getCorporation(character['corporation_id'])  # Bovril
        print("getCorporation: {}".format(corp))
    li = ["B-7DFU", "Jita"]
    ids = esi.getSystemIds(li)
    if ids:
        print("getSystemIds: {}".format(ids))
        li = []
        sys = ids['systems']
        for a in sys:
            li.append(a['id'])
        names = esi.getSystemNames(li)
        if names:
            print("getSystemNames: {}".format(names))
    jump_result, expiry = EsiInterface().getJumps()
    if jump_result:
        print("getJumps :{} {}".format(jump_result, expiry))
        jumpData = {}
        for data in jump_result:
            jumpData[int(data['system_id'])] = int(data['ship_jumps'])
    kill_result, expiry = EsiInterface().getKills()
    if kill_result:
        print("getKils :{} {}".format(kill_result, expiry))

    app.exec_()
