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
import requests

LOGGER = logging.getLogger(__name__)


class Bridges(list):
    def export(self) -> list:
        """search for duplicates and return
        """
        bridge_list = []
        for bridge in self:
            routes = [bridge.start, bridge.direction, bridge.end]
            bridge_list.append(routes)
        return bridge_list


class Bridge(object):
    """a Jump-Bridge within a Region.
    """
    def __init__(
        self,
        region: str,
        start: str,
        end: str,
        status: str = "Online",
        distance: str = "0.0",
        direction: str = "<>",
    ):
        self.region = u"{}".format(region)
        self.start = u"{}".format(start)
        self.end = u"{}".format(end)
        self.status = status
        self.distance = float(distance)
        self.direction = direction


class Import:
    """convert known formats into an internal Jump-Bridge-Structure.
    """

    def _convert_garpa_data(self, data_list: list):
        bridges = Bridges()
        for line in data_list:
            line = re.sub("[ \t]+", " ", line)
            if line.find("@") == -1:
                continue
            columns = line.split(" ")
            if len(columns) < 13:
                continue
            if columns[2] != "@" or columns[5] != "@":
                continue
            the_bridge = Bridge(
                    region=columns[0],
                    start=columns[1],
                    end=columns[4],
                    status=columns[7],
                    distance=columns[10]
                )
            for cur_bridge in bridges:
                if cur_bridge.start == the_bridge.end and cur_bridge.end == the_bridge.start:
                    the_bridge = None
                    break
            if the_bridge is not None:
                bridges.append(the_bridge)
        if len(bridges) == 0:
            # maybe it's already in Export-Format?
            for line in data_list:
                line = re.sub("[ \t]+", " ", line)
                columns = line.split(" ")
                if len(columns) != 3:
                    break
                the_bridge = Bridge(
                        region="",
                        start=columns[0],
                        end=columns[2],
                        direction=columns[1]
                    )

                for cur_bridge in bridges:
                    if cur_bridge.start == the_bridge.end and cur_bridge.end == the_bridge.start:
                        the_bridge = None
                        break
                if the_bridge is not None:
                    bridges.append(the_bridge)

        return bridges.export()

    def garpa_data(self, any_data_source: str) -> list:
        if any_data_source.strip() != "":
            import_data = ""
            if any_data_source.strip().startswith("http"):
                try:
                    import_data = requests.get(any_data_source.strip()).text.splitlines(keepends=False)
                except ConnectionError:
                    pass
            else:
                try:
                    with open(any_data_source.strip(), "rt") as file:
                        import_data = file.read().splitlines(keepends=False)
                except FileNotFoundError:
                    import_data = any_data_source.splitlines(keepends=False)
                    pass
            if len(import_data):
                return self._convert_garpa_data(import_data)
        return []


if __name__ == "__main__":
    importFile = "http://vintel.tschache.com/logfiles/goon_jump.txt"

    data = Import().garpa_data(importFile)
    print(data)
