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

from vi.dotlan.colorjavascript import ColorJavaScript
from vi.states import State


class System:
    def __init__(
        self, name, svg_element, map_soup, map_coordinates, transform, system_id
    ):
        self.status = State["UNKNOWN"]
        self.name = name
        self.svg_element = svg_element
        self.map_soup = map_soup
        self.origsvg_element = svg_element
        self.rect = svg_element.select("rect")[0]
        self.firstLine = svg_element.select("text")[0]
        self.secondLine = svg_element.select("text")[1]
        self.lastAlarmTime = 0
        self.messages = []
        self.setStatus(State["UNKNOWN"])
        self._locatedCharacters = []
        self.backgroundColor = "#FFFFFF"
        self.map_coordinates = map_coordinates
        self.system_id = system_id
        self.transform = transform
        self.cachedOffsetPoint = None
        self._neighbours = set()
        self.statistics = {
            "jumps": "?",
            "shipkills": "?",
            "factionkills": "?",
            "podkills": "?",
        }
        self.timerload = ()
        self.name_label = self.name.replace("-", "_").lower()
        self.rectId = self.svg_element.select("rect")[0]["id"]
        if len(self.svg_element.select("rect")) > 1:
            self.rectIce = self.svg_element.select("rect")[1]
        else:
            self.rectIce = self.rect
        if not self.rectIce.has_attr("id"):
            self.rectIce["id"] = "icerect{}".format(self.name_label)
        self.rectIdIce = self.rectIce["id"]
        if not self.secondLine.has_attr("id"):
            self.secondLine["id"] = "watch{}".format(self.name_label)
        # set default to White
        for rect in self.svg_element.select("rect"):
            rect["style"] = "fill: #ffffff"

    @property
    def mapCoordinates(self):
        return self.map_coordinates

    def add_message(self, message):
        if not self.messages:
            self.messages = []
        self.messages.append(message)

    def del_message(self, message):
        if message in self.messages:
            self.messages.remove(message)

    def getTransformOffsetPoint(self):
        if not self.cachedOffsetPoint:
            if self.transform:
                # Convert data in the form 'transform(0,0)' to a list of two floats
                pointString = self.transform[9:].strip("()").split(",")
                self.cachedOffsetPoint = [float(pointString[0]), float(pointString[1])]
            else:
                self.cachedOffsetPoint = [0.0, 0.0]
        return self.cachedOffsetPoint

    def setJumpbridgeColor(self, color):
        idName = u"JB_" + self.name + u"_jb_marker"
        for element in self.map_soup.select(u"#" + idName):
            element.decompose()
        coords = self.map_coordinates
        offsetPoint = self.getTransformOffsetPoint()
        x = coords["x"] - 3 + offsetPoint[0]
        y = coords["y"] + offsetPoint[1]
        style = "fill:{0};stroke:{0};stroke-width:2;fill-opacity:0.4"
        tag = self.map_soup.new_tag(
            "rect",
            x=x,
            y=y,
            width=coords["width"] + 1.5,
            height=coords["height"],
            id=idName,
            style=style.format(color),
            visibility="hidden",
        )
        tag["class"] = [
            "jumpbridge",
        ]
        jumps = self.map_soup.select("#jumps")[0]
        jumps.insert(0, tag)

    def mark(self):
        marker = self.map_soup.select("#select_marker")[0]
        offsetPoint = self.getTransformOffsetPoint()
        x = self.map_coordinates["center_x"] + offsetPoint[0]
        y = self.map_coordinates["center_y"] + offsetPoint[1]
        marker["transform"] = "translate({x},{y})".format(x=x, y=y)
        marker["opacity"] = "1"
        marker["activated"] = time.time()

    def addLocatedCharacter(self, charname):
        idName = self.getSoupId()
        wasLocated = bool(self._locatedCharacters)
        if charname not in self._locatedCharacters:
            self._locatedCharacters.append(charname)
        if not wasLocated:
            coords = self.map_coordinates
            newTag = self.map_soup.new_tag(
                "ellipse",
                cx=coords["center_x"] - 2.5,
                cy=coords["center_y"],
                id=idName,
                rx=coords["width"] / 2 + 4,
                ry=coords["height"] / 2 + 4,
                style="fill:#8b008d",
                transform=self.transform,
            )
            jumps = self.map_soup.select("#jumps")[0]
            jumps.insert(0, newTag)

    def setBackgroundColor(self, color):
        for rect in self.svg_element("rect"):
            if "location" not in rect.get("class", []) and "marked" not in rect.get(
                "class", []
            ):
                rect["style"] = "fill: {0};".format(color)

    def getLocatedCharacters(self):
        characters = []
        for char in self._locatedCharacters:
            characters.append(char)
        return characters

    def getSoupId(self):
        name_id = str(self.name)
        return "loc_" + name_id.replace("-", "_").lower()

    def removeLocatedCharacter(self, charname):
        idName = self.getSoupId()
        # idName = self.name + u"_loc"

        if charname in self._locatedCharacters:
            self._locatedCharacters.remove(charname)
            if not self._locatedCharacters:
                for element in self.map_soup.select("#" + idName):
                    element.decompose()

    def addNeighbour(self, neighbourSystem):
        """
            Add a neigbour system to this system
            neighbour_system: a system (not a system's name!)
        """
        self._neighbours.add(neighbourSystem)
        neighbourSystem._neighbours.add(self)

    def getNeighbours(self, distance=1):
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
        currentDistance = 0
        while currentDistance < distance:
            currentDistance += 1
            newSystems = []
            for system in systems.keys():
                for neighbour in system._neighbours:
                    if neighbour not in systems:
                        newSystems.append(neighbour)
            for newSystem in newSystems:
                systems[newSystem] = {"distance": currentDistance}
        return systems

    def removeNeighbour(self, system):
        """
            Removes the link between to neighboured systems
        """
        if system in self._neighbours:
            self._neighbours.remove(system)
        if self in system._neighbours:
            system._neigbours.remove(self)

    def setStatistics(self, statistics):
        if statistics is None:
            text = "stats n/a"
        else:
            text = "j-{jumps} f-{factionkills} s-{shipkills} p-{podkills}".format(
                **statistics
            )
        svgtext = self.map_soup.select("#stats_" + str(self.system_id))[0]
        svgtext.string = text

    def setStatus(self, new_status, alarm_time: float = time.time()):
        if not isinstance(alarm_time, float):
            if isinstance(alarm_time, datetime.datetime):
                alarm_time = (
                    time.mktime(alarm_time.timetuple()) + alarm_time.microsecond / 1e6
                )
                # alarm_time = (alarm_time - datetime.datetime(1970, 1, 1)).total_seconds()
        if new_status in (State["ALARM"], State["CLEAR"], State["REQUEST"]):
            self.lastAlarmTime = alarm_time
            if new_status == State["ALARM"]:
                self.secondLine["alarmtime"] = self.lastAlarmTime
            elif new_status == State["CLEAR"]:
                self.secondLine["alarmtime"] = self.lastAlarmTime
                self.secondLine.string = State["CLEAR"].value
            elif new_status == State["REQUEST"]:
                self.secondLine.string = "status"
        elif new_status == State["UNKNOWN"]:
            self.secondLine.string = "?"
        # if new_status not in (states.NOT_CHANGE, states.REQUEST):  # unknown not affect system status
        if new_status not in (State["NOT_CHANGE"],):  # unknown not affect system status
            self.status = new_status
            self.secondLine["state"] = State["NOT_CHANGE"].value

    def update(self, cjs: ColorJavaScript) -> bool:
        updated = False
        # calc the new timer for injecting into JS
        diff = max(0, math.floor(time.time() - self.lastAlarmTime))
        # diff = time.time() - self.lastAlarmTime
        minutes = int(math.floor(diff / 60))
        seconds = int(diff - minutes * 60)
        ndiff = int(minutes * 60 + seconds)
        # if self.status != states.UNKNOWN and (diff < 0 or ndiff > cjs.max_time(self.status)):  # anything older than max color-size
        #     self.setStatus(states.UNKNOWN)
        if self.status != State["UNKNOWN"]:
            self.secondLine.string = "{m:02d}:{s:02d}".format(m=minutes, s=seconds)
            self.timerload = (
                ndiff,
                self.status.value,
                self.secondLine["id"],
                self.rectId,
                self.rectIdIce,
            )
            color, text_color = cjs.color_at(ndiff, self.status)
            updated = True
            for rect in self.svg_element.select("rect"):
                rect["style"] = "fill: " + color
            self.secondLine["style"] = "fill: " + text_color
        else:
            self.secondLine.string = "??"
            self.timerload = ()
        return updated

    def __repr__(self):
        la = datetime.datetime.utcfromtimestamp(self.lastAlarmTime)
        no = datetime.datetime.utcfromtimestamp(time.time())
        ret_str = "%s: Alarm: %f (%s) (Diff: from NOW %f (%s) = %f)  (%s)" % (
            self.name,
            self.lastAlarmTime,
            la,
            time.time(),
            no,
            time.time() - self.lastAlarmTime,
            (
                ",".join(
                    "{}.{}".format(key, val) for key, val in self.statistics.items()
                )
            ),
        )
        return ret_str
