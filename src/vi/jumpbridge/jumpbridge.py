#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
from bs4 import BeautifulSoup
from math import sqrt
import requests
import re
import logging
from vi.dotlan.system import System
from vi.stopwatch.mystopwatch import ViStopwatch

class Bridge:
    """a bridge between two systems.
    This is based on how it is stored in the String-List
    """
    def __init__(self, current_systems: System, bridge_data: list, color_data: str, timer: ViStopwatch = None, index: int = 0):
        self.bridge = bridge_data
        self.color = color_data
        self.sys1 = self.bridge[0]
        self.connection = self.bridge[1]
        self.sys2 = self.bridge[2]
        self.systems = current_systems
        self.line = None
        self.sw = timer
        self.index = index

    def build(self, soup) -> BeautifulSoup.text:
        if not (self.sys1 in self.systems and self.sys2 in self.systems):
            return None
        systemOne = self.systems[self.sys1]
        systemTwo = self.systems[self.sys2]
        with self.sw.timer(f"set jumpbridge color {self.index}"):
            # this deletes the JB from Soup and re-inserts... takes time (60ms per system)
            systemOne.setJumpbridgeColor(self.color)
            systemTwo.setJumpbridgeColor(self.color)

        def arc_link(point_1, point_2, radius) -> str:
            cx = (point_1[0] + point_2[0]) / 2
            cy = (point_1[1] + point_2[1]) / 2
            dx = (point_2[0] - point_1[0]) / 2
            dy = (point_2[1] - point_1[1]) / 2
            dd = sqrt(dx * dx + dy * dy)
            ex = cx + dy/dd * radius
            ey = cy - dx/dd * radius
            return "M{x1:.2f} {y1:.2f}Q{ex:.2f} {ey:.2f} {x2:.2f} {y2:.2f}".format(
                x1=point_1[0],
                y1=point_1[1],
                ex=ex,
                ey=ey,
                x2=point_2[0],
                y2=point_2[1],
            )

        system_one = [sum(x) for x in zip(systemOne.map_points, systemOne.getTransformOffsetPoint())]
        system_two = [sum(x) for x in zip(systemTwo.map_points, systemTwo.getTransformOffsetPoint())]
        arc_str = arc_link(system_one, system_two, 40)
        with self.sw.timer(f"build soup {self.index}"):
            self.line = soup.new_tag(
                "path",
                d=arc_str,
                visibility="hidden",
                style="stroke:{0}".format(self.color),
                fill="none",
            )
            self.line["stroke-width"] = 2
            self.line["class"] = [
                "jumpbridge",
            ]
            if "<" in self.connection:
                self.line["marker-start"] = "url(#arrowstart_{0})".format(self.color.strip("#"))
            if ">" in self.connection:
                self.line["marker-end"] = "url(#arrowend_{0})".format(self.color.strip("#"))
        return self.line


class Jumpbridge:
    JB_COLORS = (
        "#800000",
        "#808000",
        "#BC8F8F",
        "#ff00ff",
        "#c83737",
        "#FF6347",
        "#917c6f",
        "#ffcc00",
        "#88aa00",
        "#FFE4E1",
        "#008080",
        "#00BFFF",
        "#4682B4",
        "#00FF7F",
        "#7FFF00",
        "#ff6600",
        "#CD5C5C",
        "#FFD700",
        "#66CDAA",
        "#AFEEEE",
        "#5F9EA0",
        "#FFDEAD",
        "#696969",
        "#2F4F4F",
    )

    def __init__(self, system, soup, jumpbridge_data):
        """Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        self.soup = soup
        self.jump_locations = self.soup.select("#jumps")[0]
        self.jump_bridge_data = jumpbridge_data
        self.system = system
        self.sw = ViStopwatch()
        self.logger = logging.getLogger(__name__)

    def clear(self):
        # destroy any previous bridges that may exist
        for bridge in self.soup.select(".jumpbridge"):
            bridge.decompose()

    def build(self):
        color_count = 0
        with self.sw.timer("Build"):
            with self.sw.timer("clear"):
                self.clear()
            bridges = []
            with self.sw.timer("calculate"):
                for index, bridge_data in enumerate(self.jump_bridge_data):
                    if color_count > len(self.JB_COLORS) - 1:
                        color_count = 0
                    jb_color = self.JB_COLORS[color_count]
                    color_count += 1
                    bridge = Bridge(self.system, bridge_data, jb_color, timer=self.sw, index=index)
                    location = bridge.build(self.soup)
                    if location:
                        yield index
                        bridges.append(location)
            with self.sw.timer("insert"):
                for location in bridges:
                    self.jump_locations.insert(0, location)
                # with self.sw.timer("yield"):
                #     yield index
        self.logger.debug(self.sw.get_report())


class Import:
    """convert known formats into an internal Jump-Bridge-Structure.
    """

    class Bridges(list):
        def export(self) -> list:
            """search for duplicates and return
            """
            bridge_list = []
            for bridge in self:
                routes = [bridge.start, bridge.direction, bridge.end]
                bridge_list.append(routes)
            return bridge_list

    class ImportBridge(object):
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

    def _convert_garpa_data(self, data_list: list):
        bridges = Import.Bridges()
        for line in data_list:
            line = re.sub("[ \t]+", " ", line)
            if line.find("@") == -1:
                continue
            columns = line.split(" ")
            if len(columns) < 13:
                continue
            if columns[2] != "@" or columns[5] != "@":
                continue
            the_bridge = Import.ImportBridge(
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
                the_bridge = Import.ImportBridge(
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
