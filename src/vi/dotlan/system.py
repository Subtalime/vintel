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

import time
import datetime
import math
from vi import states


class System(object):
    """
        A System on the Map
    """
    ALARM_COLORS = [(60 * 4, "#FF0000", "#FFFFFF"), (60 * 10, "#FF9B0F", "#FFFFFF"), (60 * 15, "#FFFA0F", "#000000"),
                    (60 * 25, "#FFFDA2", "#000000"), (60 * 60 * 24, "#FFFFFF", "#000000")]
    ALARM_COLOR = ALARM_COLORS[0][1]
    UNKNOWN_COLOR = "#FFFFFF"
    CLEAR_COLOR = "#59FF6C"

    def __init__(self, name, svgElement, mapSoup, mapCoordinates, transform, systemId):
        self.status = states.UNKNOWN
        self.name = name
        self.svgElement = svgElement
        self.mapSoup = mapSoup
        self.origSvgElement = svgElement
        self.rect = svgElement.select("rect")[0]
        self.firstLine = svgElement.select("text")[0]
        self.secondLine = svgElement.select("text")[1]
        self.lastAlarmTime = 0
        self.messages = []
        self.setStatus(states.UNKNOWN)
        self._locatedCharacters = []
        self.backgroundColor = "#FFFFFF"
        self.mapCoordinates = mapCoordinates
        self.systemId = systemId
        self.transform = transform
        self.cachedOffsetPoint = None
        self._neighbours = set()
        self.statistics = {"jumps": "?", "shipkills": "?", "factionkills": "?", "podkills": "?"}

    def getTransformOffsetPoint(self):
        if not self.cachedOffsetPoint:
            if self.transform:
                # Convert data in the form 'transform(0,0)' to a list of two floats
                pointString = self.transform[9:].strip('()').split(',')
                self.cachedOffsetPoint = [float(pointString[0]), float(pointString[1])]
            else:
                self.cachedOffsetPoint = [0.0, 0.0]
        return self.cachedOffsetPoint

    def setJumpbridgeColor(self, color):
        idName = u"JB_" + self.name + u"_jb_marker"
        for element in self.mapSoup.select(u"#" + idName):
            element.decompose()
        coords = self.mapCoordinates
        offsetPoint = self.getTransformOffsetPoint()
        x = coords["x"] - 3 + offsetPoint[0]
        y = coords["y"] + offsetPoint[1]
        style = "fill:{0};stroke:{0};stroke-width:2;fill-opacity:0.4"
        tag = self.mapSoup.new_tag("rect", x=x, y=y, width=coords["width"] + 1.5, height=coords["height"], id=idName,
                                   style=style.format(color), visibility="hidden")
        tag["class"] = ["jumpbridge", ]
        jumps = self.mapSoup.select("#jumps")[0]
        jumps.insert(0, tag)

    def mark(self):
        marker = self.mapSoup.select("#select_marker")[0]
        offsetPoint = self.getTransformOffsetPoint()
        x = self.mapCoordinates["center_x"] + offsetPoint[0]
        y = self.mapCoordinates["center_y"] + offsetPoint[1]
        marker["transform"] = "translate({x},{y})".format(x=x, y=y)
        marker["opacity"] = "1"
        marker["activated"] = time.time()

    def addLocatedCharacter(self, charname):
        idName = self.getSoupId()
        # idName = self.name + u"_loc"
        wasLocated = bool(self._locatedCharacters)
        if charname not in self._locatedCharacters:
            self._locatedCharacters.append(charname)
        if not wasLocated:
            coords = self.mapCoordinates
            newTag = self.mapSoup.new_tag("ellipse", cx=coords["center_x"] - 2.5, cy=coords["center_y"], id=idName,
                                          rx=coords["width"] / 2 + 4, ry=coords["height"] / 2 + 4, style="fill:#8b008d",
                                          transform=self.transform)
            jumps = self.mapSoup.select("#jumps")[0]
            jumps.insert(0, newTag)

    def setBackgroundColor(self, color):
        for rect in self.svgElement("rect"):
            if "location" not in rect.get("class", []) and "marked" not in rect.get("class", []):
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
                for element in self.mapSoup.select("#" + idName):
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

    def setStatus(self, newStatus, alarmtime: float = time.time()):
        if not isinstance(alarmtime, float):
            if isinstance(alarmtime, datetime.datetime):
                alarmtime = (alarmtime - datetime.datetime(1970, 1,1)).total_seconds()
        if newStatus == states.ALARM:
            self.lastAlarmTime = alarmtime
            self.secondLine["alarmtime"] = self.lastAlarmTime
        elif newStatus == states.CLEAR:
            self.lastAlarmTime = alarmtime
            self.secondLine["alarmtime"] = self.lastAlarmTime
            self.secondLine.string = "clear"
        elif newStatus == states.UNKNOWN:
            self.secondLine.string = "?"
        elif newStatus == states.REQUEST:
            self.lastAlarmTime = alarmtime
            self.secondLine.string = "status"
        # if newStatus not in (states.NOT_CHANGE, states.REQUEST):  # unknown not affect system status
        if newStatus not in (states.NOT_CHANGE):  # unknown not affect system status
            self.status = newStatus
            self.secondLine["state"] = str(self.status)

    def setStatistics(self, statistics):
        if statistics is None:
            text = "stats n/a"
        else:
            text = "j-{jumps} f-{factionkills} s-{shipkills} p-{podkills}".format(**statistics)
        svgtext = self.mapSoup.select("#stats_" + str(self.systemId))[0]
        svgtext.string = text

    def update(self):
        # state changed?
        if self.status == states.ALARM:
            alarmTime = time.time() - self.lastAlarmTime
            for maxDiff, alarmColor, secondLineColor in self.ALARM_COLORS:
                if alarmTime < maxDiff:
                    if self.backgroundColor != alarmColor:
                        self.backgroundColor = alarmColor
                        for rect in self.svgElement("rect"):
                            if "location" not in rect.get("class", []) and "marked" not in rect.get("class", []):
                                rect["style"] = "fill: {0};".format(self.backgroundColor)
                        self.secondLine["style"] = "fill: {0};".format(secondLineColor)
                    break
        if self.status in (states.ALARM, states.WAS_ALARMED, states.CLEAR):  # timer
            diff = math.floor(time.time() - self.lastAlarmTime)
            minutes = int(math.floor(diff / 60))
            seconds = int(diff - minutes * 60)
            string = "{m:02d}:{s:02d}".format(m=minutes, s=seconds)
            if self.status == states.CLEAR:
                secondsUntilWhite = 10 * 60
                calcValue = int(diff / (secondsUntilWhite / 255.0))
                if calcValue > 255:
                    calcValue = 255
                    self.secondLine["style"] = "fill: #008100;"
                string = "clr: {m:02d}:{s:02d}".format(m=minutes, s=seconds)
                self.setBackgroundColor("rgb({r},{g},{b})".format(r=calcValue, g=255, b=calcValue))
            self.secondLine.string = string

    def __repr__(self):
        return "{}:".format(self.name) + (",".join("{}.{}".format(key, val) for key, val in self.statistics.items()))
