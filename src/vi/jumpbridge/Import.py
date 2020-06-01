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

import logging
import re

LOGGER = logging.getLogger(__name__)


class Bridges(list):
    def export(self):
        bridgeList = []
        for bridge in self:
            routes = [bridge.start, bridge.direction, bridge.end]
            bridgeList.append(routes)
        return bridgeList


class Bridge(object):
    def __init__(
        self,
        region: str,
        start: str,
        end: str,
        status: str = "Online",
        distance: float = 0.0,
        direction: str = "<>",
    ):
        self.region = u"{}".format(region)
        self.start = u"{}".format(start)
        self.end = u"{}".format(end)
        self.status = status
        self.distance = float(distance)
        self.direction = direction


class Import:
    def __init__(self):
        self.bridges = Bridges()

    def convertGarpaData(self, fileContent: list):
        self.bridges.clear()
        for line in fileContent:
            line = re.sub("[ \t]+", " ", line)
            if line.find("@") == -1:
                continue
            columns = line.split(" ")
            if len(columns) < 13:
                continue
            if columns[2] != "@" or columns[5] != "@":
                continue

            self.bridges.append(
                Bridge(columns[0], columns[1], columns[4], columns[7], columns[10])
            )
        if len(self.bridges) == 0:
            # maybe it's already in Export-Format?
            for line in fileContent:
                line = re.sub("[ \t]+", " ", line)
                columns = line.split(" ")
                if len(columns) != 3:
                    break
                self.bridges.append(
                    Bridge(None, columns[0], columns[2], direction=columns[1])
                )

        return self.bridges.export()

    def readGarpaFile(self, file_name: str = None, clipboard: str = None):
        try:
            if not clipboard:
                with open(file_name, "r") as f:
                    content = f.read().splitlines(keepends=False)
            else:
                content = clipboard.splitlines(keepends=False)
            if content:
                return self.convertGarpaData(content)
        except Exception as e:
            LOGGER.error(
                "Error in importing Garpa Jumpbridges: %s, %r" % (file_name, e)
            )
        return []


if __name__ == "__main__":
    importFile = "D:\\Develop\\vintel\\src\\vi\\ui\\res\\mapdata\\Goons-jump.txt"

    data = Import().readGarpaFile(importFile)
    print(data)
