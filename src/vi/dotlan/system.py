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

import datetime
import math
import time
import logging
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.states import State
from vi.dotlan.soups import SoupSystem, SoupUse, SoupRect
from vi.stopwatch.mystopwatch import ViStopwatch


class System:
    """represent a system within the region.
    """

    messages = []
    timerload = set()
    status = State["UNKNOWN"]
    last_alarm_time = 0
    _locatedCharacters = []
    backgroundColor = "#FFFFFF"
    _neighbours = set()

    def __init__(
        self,
            name: str,
            svg_element: Tag,
            map_soup: BeautifulSoup,
            map_coordinates: dict,
            transform: list,
            system_id: int,
    ):
        self.name = name
        self.sw = ViStopwatch()
        self.LOGGER = logging.getLogger(__name__)
        self.svg_element = svg_element
        self.map_soup = map_soup
        self.rect = svg_element.select("rect")[0]
        self.firstLine = svg_element.select("text")[0]
        self._second_line = svg_element.select("text")[1]
        self.set_status(self.status)
        self._map_coordinates = map_coordinates
        self.system_id = system_id
        self.transform = transform
        self.statistics = {
            "jumps": "?",
            "shipkills": "?",
            "factionkills": "?",
            "podkills": "?",
        }
        # self.timerload = ()
        self.name_label = self.name.replace("-", "_").lower()
        self.rectId = self.svg_element.select("rect")[0]["id"]
        if len(self.svg_element.select("rect")) > 1:
            self.rectIce = self.svg_element.select("rect")[1]
        else:
            self.rectIce = self.rect
        if not self.rectIce.has_attr("id"):
            self.rectIce["id"] = "icerect{}".format(self.name_label)
        self.rectIdIce = self.rectIce["id"]
        if not self.second_line.has_attr("id"):
            self.second_line["id"] = "watch{}".format(self.name_label)
        # set default to White
        for rect in self.svg_element.select("rect"):
            rect["style"] = "fill: #ffffff"
        self.jb_name = u"JB_" + self.name + u"_jb_marker"

    @property
    def second_line(self) -> Tag:
        return self._second_line

    @property
    def map_coordinates(self) -> dict:
        return self._map_coordinates

    @property
    def map_x(self):
        return self.map_coordinates["center_x"]

    @property
    def map_y(self):
        return self.map_coordinates["center_y"]

    @property
    def map_points(self) -> [float, float]:
        return [self._map_coordinates["center_x"], self._map_coordinates["center_y"]]

    def add_message(self, message):
        """received message.
        """
        self.messages.append(message)

    def del_message(self, message):
        """purged message.
        """
        if message in self.messages:
            self.messages.remove(message)

    def get_transform_offset_point(self) -> [float, float]:
        return self.transform
        # if not self.cachedOffsetPoint:
        #     if self.transform:
        #         # Convert data in the form 'transform(0,0)' to a list of two floats
        #         point_string = self.transform[9:].strip("()").split(",")
        #         self.cachedOffsetPoint = [float(point_string[0]), float(point_string[1])]
        #     else:
        #         self.cachedOffsetPoint = [0.0, 0.0]
        # return self.cachedOffsetPoint

    def prepare_jumpbridge_color(self, color):
        """prepare a Jump-Bridge to this system with a given color.
        """
        offset_point = self.get_transform_offset_point()
        x = self.map_coordinates["x"] - 3 + offset_point[0]
        y = self.map_coordinates["y"] + offset_point[1]
        style = "fill:{0};stroke:{0};stroke-width:2;fill-opacity:0.4"
        tag = self.map_soup.new_tag(
            "rect",
            x=x,
            y=y,
            width=self.map_coordinates["width"] + 1.5,
            height=self.map_coordinates["height"],
            id=self.jb_name,
            style=style.format(color),
            visibility="hidden",
        )
        tag["class"] = [
            "jumpbridge",
        ]
        return tag

    def set_jumpbridge_color(self, color):
        """set a Jump-Bridge to this system with a given color.
        """
        for element in self.map_soup.findAll("rect", {"id": self.jb_name}):
            element.decompose()
        tag = self.prepare_jumpbridge_color(color)
        jumps = self.map_soup.findAll("g", {"id": "jumps"})[0]
        jumps.insert(0, tag)

    def mark(self):
        """show the system as marked.
        """
        marker = self.map_soup.findAll("g", {"id": "select_marker"})
        if marker:
            marker = marker[0]
        else:
            marker = self.map_soup.select("#select_marker")[0]
        offset_point = self.get_transform_offset_point()
        x = self.map_x + offset_point[0]
        y = self.map_y + offset_point[1]
        marker["transform"] = "translate({x},{y})".format(x=x, y=y)
        marker["opacity"] = "1"
        marker["activated"] = time.time()

    def add_located_character(self, charname):
        """add a known Character to this system.
        """
        id_name = self.get_soup_id()
        was_located = bool(self._locatedCharacters)
        if charname not in self._locatedCharacters:
            self._locatedCharacters.append(charname)
        if not was_located:
            coordinates = self.map_coordinates
            new_tag = self.map_soup.new_tag(
                "ellipse",
                cx=coordinates["center_x"] - 2.5,
                cy=coordinates["center_y"],
                id=id_name,
                rx=coordinates["width"] / 2 + 4,
                ry=coordinates["height"] / 2 + 4,
                style="fill:#8b008d",
                transform=f"transform({self.transform[0]},{self.transform[1]})",
            )
            # jumps = self.map_soup.select("#jumps")[0]
            jumps = self.map_soup.findAll("g", {"id": "jumps"})[0]
            jumps.insert(0, new_tag)

    def setBackgroundColor(self, color):
        for rect in self.svg_element("rect"):
            if "location" not in rect.get("class", []) and "marked" not in rect.get(
                "class", []
            ):
                rect["style"] = "fill: {0};".format(color)

    def get_located_characters(self) -> list:
        """return a list of known Characters in this system.
        """
        characters = []
        for char in self._locatedCharacters:
            characters.append(char)
        return characters

    def get_soup_id(self) -> str:
        name_id = str(self.name)
        return "loc_" + name_id.replace("-", "_").lower()

    def remove_located_character(self, charname):
        """character has moved on from this System.
        """
        id_name = self.get_soup_id()

        if charname in self._locatedCharacters:
            self._locatedCharacters.remove(charname)
            if not self._locatedCharacters:
                for element in self.map_soup.select("#" + id_name):
                    element.decompose()

    def add_neighbour(self, neighbour_system):
        """Add a neighbour system to this system
            neighbour_system: a system (not a system's name!)
        """
        self._neighbours.add(neighbour_system)

    def get_neighbour_list(self) -> set:
        return self._neighbours

    def get_neighbours(self, distance=1):
        """
            Get all neigboured system with a distance of distance.
            example: sys1 <-> sys2 <-> sys3 <-> sys4 <-> sys5
            sys3(distance=1) will find sys2, sys3, sys4
            sys3(distance=2) will find sys1, sys2, sys3, sys4, sys5
            returns a dictionary with the system (not the system's name!)
            as key and a dict as value. key "distance" contains the distance.
            example:
            {sys3: {"distance"}: 0, sys2: {"distance"}: 1}
        """
        systems = {self: {"distance": 0}}
        current_distance = 0
        while current_distance < distance:
            current_distance += 1
            new_systems = []
            for system in systems.keys():
                for neighbour in system.get_neighbour_list():
                    if neighbour not in systems:
                        new_systems.append(neighbour)
            for newSystem in new_systems:
                systems[newSystem] = {"distance": current_distance}
        return systems

    def set_statistics(self, statistics):
        if statistics is None:
            text = "stats n/a"
        else:
            text = "j-{jumps} f-{factionkills} s-{shipkills} p-{podkills}".format(
                **statistics
            )
        svg_text = self.map_soup.select("#stats_" + str(self.system_id))[0]
        svg_text.string = text

    def set_status(self, new_status, alarm_time: float = time.time()):
        if not isinstance(alarm_time, float):
            if isinstance(alarm_time, datetime.datetime):
                alarm_time = (
                    time.mktime(alarm_time.timetuple()) + alarm_time.microsecond / 1e6
                )
        if new_status in (State["ALARM"], State["CLEAR"], State["REQUEST"]):
            self.last_alarm_time = alarm_time
            if new_status == State["ALARM"]:
                self._second_line["alarmtime"] = self.last_alarm_time
            elif new_status == State["CLEAR"]:
                self._second_line["alarmtime"] = self.last_alarm_time
                self._second_line.string = State["CLEAR"].value
            elif new_status == State["REQUEST"]:
                self._second_line.string = "status"
        elif new_status == State["UNKNOWN"]:
            self._second_line.string = "?"
        # if new_status not in (states.NOT_CHANGE, states.REQUEST):  # unknown not affect system status
        if new_status not in (State["NOT_CHANGE"],):  # unknown not affect system status
            self.status = new_status
            self._second_line["state"] = State["NOT_CHANGE"].value

    def update(self, cjs: ColorJavaScript) -> bool:
        updated = False
        # calc the new timer for injecting into JS
        diff = max(0, math.floor(time.time() - self.last_alarm_time))
        # diff = time.time() - self.lastAlarmTime
        minutes = int(math.floor(diff / 60))
        seconds = int(diff - minutes * 60)
        ndiff = int(minutes * 60 + seconds)
        if self.status != State["UNKNOWN"]:
            self._second_line.string = "{m:02d}:{s:02d}".format(m=minutes, s=seconds)
            self.timerload = (
                ndiff,
                self.status.value,
                self._second_line["id"],
                self.rectId,
                self.rectIdIce,
            )
            color, text_color = cjs.color_at(ndiff, self.status)
            updated = True
            for rect in self.svg_element.findAll("rect"):
                rect["style"] = "fill: " + color
            self._second_line["style"] = "fill: " + text_color
        else:
            self._second_line.string = "??"
            self.timerload = ()
        return updated

    def __repr__(self):
        la = datetime.datetime.utcfromtimestamp(self.last_alarm_time)
        no = datetime.datetime.utcfromtimestamp(time.time())
        ret_str = "%s: Alarm: %f (%s) (Diff: from NOW %f (%s) = %f)  (%s)" % (
            self.name,
            self.last_alarm_time,
            la,
            time.time(),
            no,
            time.time() - self.last_alarm_time,
            (
                ",".join(
                    "{}.{}".format(key, val) for key, val in self.statistics.items()
                )
            ),
        )
        return ret_str


class MySystem(System):
    def __init__(self, soup_system: SoupSystem, soup: BeautifulSoup):
        super().__init__(
            soup_system.name,
            soup_system.system,
            soup,
            soup_system.rect.as_dict,
            soup_system.transform,
            soup_system.system_id,
        )
        self._system = soup_system
        self._soup = soup
        self.coordinates = self._system.rect

    def add_located_character(self, charname):
        """add a known Character to this system.
        """
        id_name = self.get_soup_id()
        was_located = bool(self._locatedCharacters)
        if charname not in self._locatedCharacters:
            self._locatedCharacters.append(charname)
        if not was_located:
            new_tag = self._soup.new_tag(
                "ellipse",
                cx=self._system.rect.cx - 2.5,
                cy=self._system.rect.cy,
                rx=self._system.rect.w / 2 + 4,
                ry=self._system.rect.h / 2 + 4,
                id=self.label,
                style="fill:#8b008d",
                transform=f"transform(0, 0)",
            )
            # jumps = self.map_soup.select("#jumps")[0]
            jumps = self._soup.findAll("g", {"id": "jumps"})[0]
            jumps.insert(0, new_tag)

    def update(self, cjs: ColorJavaScript) -> bool:
        updated = False
        # calc the new timer for injecting into JS
        diff = max(0, math.floor(time.time() - self.last_alarm_time))
        # diff = time.time() - self.lastAlarmTime
        minutes = int(math.floor(diff / 60))
        seconds = int(diff - minutes * 60)
        ndiff = int(minutes * 60 + seconds)
        if self.status != State["UNKNOWN"]:
            self._system.line_two.string = "{m:02d}:{s:02d}".format(m=minutes, s=seconds)
            self.timerload = (
                ndiff,
                self.status.value,
                self._system.line_two["id"],
                self.rectId,
                self.rectIdIce,
            )
            color, text_color = cjs.color_at(ndiff, self.status)
            updated = True
            for rect in self._system.rectangles:
                rect["style"] = "fill: " + color
            self._system.line_two["style"] = "fill: " + text_color
        else:
            self._system.line_two.string = "??"
            self.timerload = ()
        return updated

    def get_transform_offset_point(self) -> [float, float]:
        return [0., 0.]

    def prepare_jumpbridge_color(self, color):
        """prepare a Jump-Bridge to this system with a given color.
        """
        offset_point = self.get_transform_offset_point()
        x = self.coordinates.x - 3 + offset_point[0]
        y = self.coordinates.y + offset_point[1]
        style = "fill:{0};stroke:{0};stroke-width:2;fill-opacity:0.4"
        tag = self.map_soup.new_tag(
            "rect",
            x=x,
            y=y,
            width=self.coordinates.w + 1.5,
            height=self.coordinates.h,
            id=self.jb_name,
            style=style.format(color),
            visibility="hidden",
        )
        tag["class"] = [
            "jumpbridge",
        ]
        return tag

    def set_jumpbridge_color(self, color):
        """set a Jump-Bridge to this system with a given color.
        """
        for element in self.map_soup.findAll("rect", {"id": self.jb_name}):
            element.decompose()
        tag = self.prepare_jumpbridge_color(color)
        jumps = self.map_soup.findAll("g", {"id": "jumps"})[0]
        jumps.insert(0, tag)

    @property
    def name_name(self) -> str:
        """system name
        """
        return self._system.name

    @property
    def label(self) -> str:
        """name converted into a lable
        """
        return self.name.replace("-", "_").lower()

    def add_message(self, message):
        """received message.
        """
        self.messages.append(message)

    def del_message(self, message):
        """purge message.
        """
        if message in self.messages:
            self.messages.remove(message)
