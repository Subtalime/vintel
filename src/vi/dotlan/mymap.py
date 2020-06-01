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
import logging
import os
import re
import sys
import time

from bs4.element import CData
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets
from vi.cache import Cache
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.dotlan.jumpbridge import Jumpbridge
from vi.dotlan.system import System
from vi.dotlan.exception import DotlanException
from vi.esi import EsiInterface
from vi.logger.mystopwatch import ViStopwatch
from vi.resources import getVintelMap
from vi.states import State
import requests


class MapData:
    """get the SVG content from wherever it resides.
    """

    DOTLAN_BASE_URL = u"http://evemaps.dotlan.net/svg/{0}.svg"

    def __init__(self, region: str):
        self.region = region
        self.svg = None

    def _get_svg_from_dotlan(self):
        url = self.DOTLAN_BASE_URL.format(self.region)
        try:
            content = requests.get(url).text
            if content.startswith("region not found"):
                raise DotlanException(content)
        except Exception as e:
            raise DotlanException(e)
        return content

    def from_dotlan(self):
        self.svg = self._get_svg_from_dotlan()
        Cache().put(
            "map_" + self.region,
            self.svg,
            EsiInterface().secondsTillDowntime() + 60 * 60,
        )

    def fix_svg(self):
        # replace the header to show encoding
        self.svg = re.sub(
            r"<\?xml.*\?>", r'<?xml version="1.0" encoding="ISO-8859-1"?>', self.svg,
        )

    def from_cache(self):
        self.svg = Cache().fetch("map_" + self.region)
        if not self.svg:
            raise

    def from_file(self):
        file_path = getVintelMap(regionName=self.region)
        with open(file_path, "r") as f:
            self.svg = f.read()

    def load(self):
        # try in sequence
        try:
            self.from_cache()
        except:
            try:
                self.from_file()
            except:
                try:
                    self.from_dotlan()
                except DotlanException as e:
                    t = (
                        "No Map in cache, nothing from dotlan. Must give up "
                        "because this happened:\n{0} {1}\n\nThis could be a "
                        "temporary problem (like dotlan is not reachable), or "
                        "everythig went to hell. Sorry. This makes no sense "
                        "without the map.".format(type(e), e)
                    )
                    raise DotlanException(t)
        self.fix_svg()
        return self.svg


class MyMap:
    def __init__(self, parent, region):
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.debug("Initializing Map for {}".format(region))
        self.region = region
        self.parent = parent
        self.progress = None
        self.sw = ViStopwatch()
        self.system_updates = 0
        self.soup = None
        self.systems = None
        self._jumpMapsVisible = False
        self._statisticsVisible = False

        svg = MapData(self.region).load()
        if self.parent:
            if not self.progress:
                self.progress = QtWidgets.QProgressDialog(
                    "Loading map data...", "", 0, 1, self.parent
                )
                self.progress.setModal(False)

        # Create soup from the svg
        self.soup = BeautifulSoup(svg, "html.parser")
        self.systems = self._extractSystemsFromSoup()
        self.systemsById = {}
        for system in self.systems.values():
            self.systemsById[system.system_id] = system
        self._prepareSvg()
        self._connectNeighbours()
        self.marker = self.soup.select("#select_marker")[0]
        self.LOGGER.debug("Initializing Map for {}: Done".format(region))
        if self.parent:
            # this closes...
            self.progress.setValue(1)
            self.progress = None

    def _extractSystemsFromSoup(self):
        systems = {}
        uses = {}
        for use in self.soup.select("use"):
            useId = use["xlink:href"][1:]
            uses[useId] = use
        symbols = self.soup.select("symbol")
        for symbol in symbols:
            symbolId = symbol["id"]
            systemId = symbolId[3:]
            try:
                systemId = int(systemId)
            except ValueError:
                continue
            for element in symbol.select(".sys"):
                name = element.select("text")[0].text.strip().upper()
                mapCoordinates = {}
                for keyname in ("x", "y", "width", "height"):
                    mapCoordinates[keyname] = float(uses[symbolId][keyname])
                mapCoordinates["center_x"] = mapCoordinates["x"] + (
                    mapCoordinates["width"] / 2
                )
                mapCoordinates["center_y"] = mapCoordinates["y"] + (
                    mapCoordinates["height"] / 2
                )
                try:
                    transform = uses[symbolId]["transform"]
                except KeyError:
                    transform = "translate(0,0)"
                systems[name] = System(
                    name, element, self.soup, mapCoordinates, transform, systemId
                )
        return systems

    def _prepareSvg(self):
        svg = self.soup.select("svg")[0]
        # Disable dotlan mouse functionality and make all jump lines black
        svg["onmousedown"] = "return false;"
        for line in self.soup.select("line"):
            line["class"] = "j"

        # Current system marker ellipse
        group = self.soup.new_tag(
            "g",
            id="select_marker",
            opacity="0",
            activated="0",
            transform="translate(0, 0)",
        )
        ellipse = self.soup.new_tag(
            "ellipse", cx="0", cy="0", rx="56", ry="28", style="fill:#462CFF"
        )
        group.append(ellipse)

        # The giant cross-hairs
        for coord in ((0, -10000), (-10000, 0), (10000, 0), (0, 10000)):
            line = self.soup.new_tag(
                "line", x1=coord[0], y1=coord[1], x2="0", y2="0", style="stroke:#462CFF"
            )
            group.append(line)
        svg.insert(0, group)

        # Create jumpbridge markers in a variety of colors
        for jbColor in Jumpbridge.JB_COLORS:
            startPath = self.soup.new_tag("path", d="M 10 0 L 10 10 L 0 5 z")
            startMarker = self.soup.new_tag(
                "marker",
                viewBox="0 0 20 20",
                id="arrowstart_{0}".format(jbColor),
                markerUnits="strokeWidth",
                markerWidth="20",
                markerHeight="15",
                refx="-15",
                refy="5",
                orient="auto",
                style="stroke:#{0};fill:#{0}".format(jbColor),
            )
            startMarker.append(startPath)
            svg.insert(0, startMarker)
            endpath = self.soup.new_tag("path", d="M 0 0 L 10 5 L 0 10 z")
            endmarker = self.soup.new_tag(
                "marker",
                viewBox="0 0 20 20",
                id="arrowend_{0}".format(jbColor),
                markerUnits="strokeWidth",
                markerWidth="20",
                markerHeight="15",
                refx="25",
                refy="5",
                orient="auto",
                style="stroke:#{0};fill:#{0}".format(jbColor),
            )
            endmarker.append(endpath)
            svg.insert(0, endmarker)
        jumps = self.soup.select("#jumps")[0]

        # Set up the tags for system statistics
        for systemId, system in self.systemsById.items():
            coords = system.map_coordinates
            text = "stats n/a"
            style = (
                "text-anchor:middle;font-size:8;font-weight:normal;font-family:Arial;"
            )
            svgtext = self.soup.new_tag(
                "text",
                x=coords["center_x"],
                y=coords["y"] + coords["height"] + 6,
                fill="blue",
                style=style,
                visibility="hidden",
                transform=system.transform,
            )
            svgtext["id"] = "stats_" + str(systemId)
            svgtext["class"] = [
                "statistics",
            ]
            svgtext.string = text
            jumps.append(svgtext)

    def _connectNeighbours(self):
        """
            This will find all neighbours of the systems and connect them.
            It takes a look at all the jumps on the map and gets the system under
            which the line ends
        """
        for jump in self.soup.select("#jumps")[0].select(".j"):
            if "jumpbridge" in jump["class"]:
                continue
            parts = jump["id"].split("-")
            if parts[0] == "j":
                startSystem = self.systemsById[int(parts[1])]
                stopSystem = self.systemsById[int(parts[2])]
                startSystem.addNeighbour(stopSystem)

    def addSystemStatistics(self, statistics):
        self.LOGGER.info("addSystemStatistics start")
        if statistics is not None:
            for systemId, system in self.systemsById.items():
                if systemId in statistics:
                    system.setStatistics(statistics[systemId])
        else:
            for system in self.systemsById.values():
                system.setStatistics(None)
        self.LOGGER.info("addSystemStatistics complete")

    def changeStatisticsVisibility(self):
        newStatus = False if self._statisticsVisible else True
        value = "visible" if newStatus else "hidden"
        for line in self.soup.select(".statistics"):
            line["visibility"] = value
        self._statisticsVisible = newStatus
        return newStatus

    def changeJumpbridgesVisibility(self):
        newStatus = False if self._jumpMapsVisible else True
        value = "visible" if newStatus else "hidden"
        for line in self.soup.select(".jumpbridge"):
            line["visibility"] = value
        self._jumpMapsVisible = newStatus
        return newStatus

    def addTimerJs(self):
        realtime_js = ColorJavaScript().js_color_all()
        realtime_js += ColorJavaScript().show_timer()
        js = self.soup.find("script", attrs={"id": "timer", "type": "text/javascript"})
        if not js:
            js = self.soup.new_tag(
                "script", attrs={"id": "timer", "type": "text/javascript"}
            )
        js.string = CData(realtime_js)
        self.soup.svg.append(js)

    def time_report(self, extra_msg: str = None):
        self.LOGGER.debug(self.sw.get_report(extra_msg))

    def timerload(self, timerload):
        return (
            "showTimer({0}, '{1}', document.querySelector('#{2}'), "
            "document.querySelector('#{3}'), document.querySelector('#{4}'));".format(
                timerload[0], timerload[1], timerload[2], timerload[3], timerload[4],
            )
        )

    @property
    def svg(self):
        # time this complete block
        with self.sw.timer("SVG"):
            with self.sw.timer("add Timer JS"):
                self.addTimerJs()
            # Re-render all systems
            with self.sw.timer("System update"):
                onload = []
                count = 0
                cjs = ColorJavaScript()
                for system in self.systems.values():
                    if (
                        len(system.timerload) and system.timerload[0] >= 60 * 60 * 2
                    ):  # remove timers older than 2 hours
                        system.setStatus(State["UNKNOWN"])
                    # TODO: when changing System, rescan all Chats and update markers that way
                    if system.update(cjs):
                        count += 1
                        if str(system.secondLine.string).startswith("-"):
                            self.LOGGER.error(system)
                    if len(system.timerload):  # remove timers older than 2 hours
                        onload.append(self.timerload(system.timerload))
                self.system_updates = count
            # Update the OnLoad JavaScript in the page
            with self.sw.timer("add window.onload JS"):
                js_onload = self.soup.find("script", attrs={"id": "onload"})
                if not js_onload:
                    js_onload = self.soup.new_tag(
                        "script", attrs={"id": "onload", "type": "text/javascript"}
                    )
                    self.soup.svg.append(js_onload)
                js_onload = self.soup.find("script", attrs={"id": "onload"})
                if len(onload) > 0:
                    startjs = "window.onload = function () {\n"
                    for load in onload:
                        startjs += load + "\n"
                    startjs += "};\n"
                    js_onload.string = startjs
            # Update the marker
            with self.sw.timer("Update Opacity Marker"):
                if not self.marker["opacity"] == "0":
                    now = time.time()
                    new_value = 1 - (now - float(self.marker["activated"])) / 10
                    if new_value < 0:
                        new_value = "0"
                    self.marker["opacity"] = new_value
            with self.sw.timer("Build Map Content"):
                content = str(self.soup)
            if not getattr(sys, "frozen", False):
                with self.sw.timer("Dump Map To disc"):
                    # pass
                    self.debugWriteSoup(content)
        self.time_report("\tNumber of timers in SVG: %d" % self.system_updates)
        return content

    def debugWriteSoup(self, svgData):
        # svgData = BeautifulSoup(self.svg, 'html.parser').prettify("utf-8")
        from vi.resources import getVintelLogDir

        ts = datetime.datetime.fromtimestamp(time.time()).strftime("%H_%M_%S")
        try:
            with open(
                os.path.join(getVintelLogDir(), "zoutput_{}.svg".format(ts)), "w+"
            ) as svgFile:
                svgFile.write(svgData)
        except Exception as e:
            self.LOGGER.error(e)

    def setJumpbridges(self, jumpbridge_data, parent=None):
        """
            Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        if not jumpbridge_data or len(jumpbridge_data) <= 0:
            return
        jb_builder = Jumpbridge(self.systems, self.soup, jumpbridge_data)
        progress = QtWidgets.QProgressDialog(
            "Creating Jump-Bridge mappings...", "Abort", 0, len(jumpbridge_data), parent
        )
        progress.setWindowTitle("Jump-Bridge")
        progress.setModal(True)
        progress.setValue(0)
        jumps = 0
        for data, loc in jb_builder.build():
            jumps += 1
            if not jumps % 4:
                progress.setValue(jumps)
            if progress.wasCanceled():
                break
        progress.setValue(len(jumpbridge_data))
