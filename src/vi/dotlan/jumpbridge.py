#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2020. Steven Tschache (github@tschache.com)
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
from vi.jumpbridge.Import import Import


class Bridge:
    """a bridge between two systems.
    This is based on how it is stored in the String-List
    """
    def __init__(self, current_systems, bridge_data, color_data):
        self.bridge = bridge_data
        self.color = color_data
        self.sys1 = self.bridge[0]
        self.connection = self.bridge[1]
        self.sys2 = self.bridge[2]
        self.systems = current_systems
        self.line = None

    def build(self, soup) -> BeautifulSoup.text:
        if not (self.sys1 in self.systems and self.sys2 in self.systems):
            return None
        systemOne = self.systems[self.sys1]
        systemTwo = self.systems[self.sys2]
        systemOneCoords = systemOne.map_coordinates
        systemTwoCoords = systemTwo.map_coordinates
        systemOneOffsetPoint = systemOne.getTransformOffsetPoint()
        systemTwoOffsetPoint = systemTwo.getTransformOffsetPoint()
        systemOne.setJumpbridgeColor(self.color)
        systemTwo.setJumpbridgeColor(self.color)

        systemOnePoint = systemOne.map_points
        systemTwoPoint = systemTwo.map_points

        # Construct the line, color it and add it to the jumps
        # self.line = soup.new_tag(
        #     "line",
        #     x1=systemOneCoords["center_x"] + systemOneOffsetPoint[0],
        #     y1=systemOneCoords["center_y"] + systemOneOffsetPoint[1],
        #     x2=systemTwoCoords["center_x"] + systemTwoOffsetPoint[0],
        #     y2=systemTwoCoords["center_y"] + systemTwoOffsetPoint[1],
        #     visibility="hidden",
        #     style="stroke:#{0}".format(self.color),
        # )


        def arc_link(point_1, point_2, r) -> str:
            cx = (point_1[0] + point_2[0]) / 2
            cy = (point_1[1] + point_2[1]) / 2
            dx = (point_2[0] - point_1[0]) / 2
            dy = (point_2[1] - point_1[1]) / 2
            dd = sqrt(dx * dx + dy * dy)
            ex = cx + dy/dd * r
            ey = cy - dx/dd * r
            return "M{x1:.2f} {y1:.2f}Q{ex:.2f} {ey:.2f} {x2:.2f} {y2:.2f}".format(
                x1=point_1[0],
                y1=point_1[1],
                ex=ex,
                ey=ey,
                x2=point_2[0],
                y2=point_2[1],
            )

        system_one = [sum(x) for x in zip(systemOnePoint, systemOneOffsetPoint)]
        system_two = [sum(x) for x in zip(systemTwoPoint, systemTwoOffsetPoint)]
        self.line = soup.new_tag(
            "path",
            d=arc_link(system_one, system_two, 40,),
            visibility="hidden",
            style="stroke:#{0}".format(self.color),
            fill="none",
        )
        # self.line = soup.new_tag(
        #     "path",
        #     d="M {x1},{y1} a{x2},{y2} 0 0,1 {x2},{y2}".format(
        #         x2=systemOneCoords["center_x"] + systemOneOffsetPoint[0],
        #         y2=systemOneCoords["center_y"] + systemOneOffsetPoint[1],
        #         x1=systemTwoCoords["center_x"] + systemTwoOffsetPoint[0],
        #         y1=systemTwoCoords["center_y"] + systemTwoOffsetPoint[1],
        #     ),
        #     visibility="hidden",
        #     style="stroke:#{0}".format(self.color),
        #     fill="none",
        # )
        self.line["stroke-width"] = 2
        self.line["class"] = [
            "jumpbridge",
        ]
        if "<" in self.connection:
            self.line["marker-start"] = "url(#arrowstart_{0})".format(self.color)
        if ">" in self.connection:
            self.line["marker-end"] = "url(#arrowend_{0})".format(self.color)
        return self.line


class Jumpbridge:
    JB_COLORS = (
        "800000",
        "808000",
        "BC8F8F",
        "ff00ff",
        "c83737",
        "FF6347",
        "917c6f",
        "ffcc00",
        "88aa00",
        "FFE4E1",
        "008080",
        "00BFFF",
        "4682B4",
        "00FF7F",
        "7FFF00",
        "ff6600",
        "CD5C5C",
        "FFD700",
        "66CDAA",
        "AFEEEE",
        "5F9EA0",
        "FFDEAD",
        "696969",
        "2F4F4F",
    )

    def __init__(self, system, soup, jumpbridge_data):
        """Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        self.soup = soup
        self.jump_locations = self.soup.select("#jumps")[0]
        self.jump_bridge_data = jumpbridge_data
        self.system = system

    def clear(self):
        # destroy any previous bridges that may exist
        for bridge in self.soup.select(".jumpbridge"):
            bridge.decompose()

    def build(self):
        color_count = 0
        self.clear()
        for bridge_data in self.jump_bridge_data:
            if color_count > len(self.JB_COLORS) - 1:
                color_count = 0
            jb_color = self.JB_COLORS[color_count]
            color_count += 1
            bridge = Bridge(self.system, bridge_data, jb_color)
            location = bridge.build(self.soup)
            if location:
                self.jump_locations.insert(0, location)
            yield bridge_data, location
