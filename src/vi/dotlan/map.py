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

import time
import logging
import requests
import six
from bs4 import BeautifulSoup
from vi.esi import EsiInterface
from vi.dotlan.mysystem import MySystem as System
from vi.dotlan.exception import DotlanException
from vi.cache.cache import Cache
from vi.version import URL

LOGGER = logging.getLogger(__name__)
JB_COLORS = ("800000", "808000", "BC8F8F", "ff00ff", "c83737", "FF6347", "917c6f", "ffcc00",
             "88aa00" "FFE4E1", "008080", "00BFFF", "4682B4", "00FF7F", "7FFF00", "ff6600",
             "CD5C5C", "FFD700", "66CDAA", "AFEEEE", "5F9EA0", "FFDEAD", "696969", "2F4F4F")


class Map(object):
    """
        The map including all information from dotlan
    """

    DOTLAN_BASIC_URL = u"http://evemaps.dotlan.net/svg/{0}.svg"

    @property
    def svg(self):
        # Re-render all systems
        for system in self.systems.values():
            system.update()
        # Update the marker
        if not self.marker["opacity"] == "0":
            now = time.time()
            newValue = (1 - (now - float(self.marker["activated"])) / 10)
            if newValue < 0:
                newValue = "0"
            self.marker["opacity"] = newValue
        content = str(self.soup)
        return content

    def __init__(self, region, svgFile=None):
        LOGGER.debug("Initializing Map for {}".format(region))
        self.region = region
        cache = Cache()
        self.outdatedCacheError = None

        # Get map from dotlan if not in the cache
        if not svgFile:
            svg = cache.fetch("map_" + self.region)
        else:
            svg = svgFile
        if not svg or str(svg).startswith("region not found"):
            try:
                svg = self._getSvgFromDotlan(self.region)
                cache.put("map_" + self.region, svg,
                                   EsiInterface().secondsTillDowntime() + 60 * 60)
            except Exception as e:
                self.outdatedCacheError = e
                svg = cache.fetch("map_" + self.region, True)
                if not svg:
                    t = "No Map in cache, nothing from dotlan. Must give up " \
                        "because this happened:\n{0} {1}\n\nThis could be a " \
                        "temporary problem (like dotlan is not reachable), or " \
                        "everythig went to hell. Sorry. This makes no sense " \
                        "without the map.\n\nRemember the site for possible " \
                        "updates: {2}".format(type(e), six.text_type(e), URL)
                    raise DotlanException(t)
        # Create soup from the svg
        self.soup = BeautifulSoup(svg, 'html.parser')

        self.systems = self._extractSystemsFromSoup(self.soup)
        self.systemsById = {}
        for system in self.systems.values():
            self.systemsById[system.systemId] = system
        self._prepareSvg(self.soup, self.systems)
        self._connectNeighbours()
        self._jumpMapsVisible = False
        self._statisticsVisible = False
        self.marker = self.soup.select("#select_marker")[0]
        LOGGER.debug("Initializing Map for {}: Done".format(region))

    def _extractSystemsFromSoup(self, soup):
        systems = {}
        uses = {}
        for use in soup.select("use"):
            useId = use["xlink:href"][1:]
            uses[useId] = use
        symbols = soup.select("symbol")
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
                mapCoordinates["center_x"] = (mapCoordinates["x"] + (mapCoordinates["width"] / 2))
                mapCoordinates["center_y"] = (mapCoordinates["y"] + (mapCoordinates["height"] / 2))
                try:
                    transform = uses[symbolId]["transform"]
                except KeyError:
                    transform = "translate(0,0)"
                systems[name] = System(name, element, self.soup, mapCoordinates, transform, systemId)
        return systems

    def _prepareSvg(self, soup, systems):
        svg = soup.select("svg")[0]
        # Disable dotlan mouse functionality and make all jump lines black
        svg["onmousedown"] = "return false;"
        for line in soup.select("line"):
            line["class"] = "j"

        # Current system marker ellipse
        group = soup.new_tag("g", id="select_marker", opacity="0", activated="0", transform="translate(0, 0)")
        ellipse = soup.new_tag("ellipse", cx="0", cy="0", rx="56", ry="28", style="fill:#462CFF")
        group.append(ellipse)

        # The giant cross-hairs
        for coord in ((0, -10000), (-10000, 0), (10000, 0), (0, 10000)):
            line = soup.new_tag("line", x1=coord[0], y1=coord[1], x2="0", y2="0", style="stroke:#462CFF")
            group.append(line)
        svg.insert(0, group)

        # Create jumpbridge markers in a variety of colors
        for jbColor in JB_COLORS:
            startPath = soup.new_tag("path", d="M 10 0 L 10 10 L 0 5 z")
            startMarker = soup.new_tag("marker", viewBox="0 0 20 20", id="arrowstart_{0}".format(jbColor),
                                       markerUnits="strokeWidth", markerWidth="20", markerHeight="15", refx="-15",
                                       refy="5", orient="auto", style="stroke:#{0};fill:#{0}".format(jbColor))
            startMarker.append(startPath)
            svg.insert(0, startMarker)
            endpath = soup.new_tag("path", d="M 0 0 L 10 5 L 0 10 z")
            endmarker = soup.new_tag("marker", viewBox="0 0 20 20", id="arrowend_{0}".format(jbColor),
                                     markerUnits="strokeWidth", markerWidth="20", markerHeight="15", refx="25",
                                     refy="5", orient="auto", style="stroke:#{0};fill:#{0}".format(jbColor))
            endmarker.append(endpath)
            svg.insert(0, endmarker)
        jumps = soup.select("#jumps")[0]

        # Set up the tags for system statistics
        for systemId, system in self.systemsById.items():
            coords = system.mapCoordinates
            text = "stats n/a"
            style = "text-anchor:middle;font-size:8;font-weight:normal;font-family:Arial;"
            svgtext = soup.new_tag("text", x=coords["center_x"], y=coords["y"] + coords["height"] + 6, fill="blue",
                                   style=style, visibility="hidden", transform=system.transform)
            svgtext["id"] = "stats_" + str(systemId)
            svgtext["class"] = ["statistics", ]
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

    def _getSvgFromDotlan(self, region):
        url = self.DOTLAN_BASIC_URL.format(region)
        content = requests.get(url).text
        if content.startswith("region not found"):
            raise Exception(content)
        return content

    def addSystemStatistics(self, statistics):
        LOGGER.info("addSystemStatistics start")
        if statistics is not None:
            for systemId, system in self.systemsById.items():
                if systemId in statistics:
                    system.setStatistics(statistics[systemId])
        else:
            for system in self.systemsById.values():
                system.setStatistics(None)
        LOGGER.info("addSystemStatistics complete")

    def setJumpbridges(self, jumpbridgesData):
        """
            Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        soup = self.soup
        for bridge in soup.select(".jumpbridge"):
            bridge.decompose()
        jumps = soup.select("#jumps")[0]
        colorCount = 0

        for bridge in jumpbridgesData:
            sys1 = bridge[0]
            connection = bridge[1]
            sys2 = bridge[2]
            if not (sys1 in self.systems and sys2 in self.systems):
                continue

            if colorCount > len(JB_COLORS) - 1:
                colorCount = 0
            jbColor = JB_COLORS[colorCount]
            colorCount += 1
            systemOne = self.systems[sys1]
            systemTwo = self.systems[sys2]
            systemOneCoords = systemOne.mapCoordinates
            systemTwoCoords = systemTwo.mapCoordinates
            systemOneOffsetPoint = systemOne.getTransformOffsetPoint()
            systemTwoOffsetPoint = systemTwo.getTransformOffsetPoint()

            systemOne.setJumpbridgeColor(jbColor)
            systemTwo.setJumpbridgeColor(jbColor)

            # Construct the line, color it and add it to the jumps
            line = soup.new_tag("line", x1=systemOneCoords["center_x"] + systemOneOffsetPoint[0],
                                y1=systemOneCoords["center_y"] + systemOneOffsetPoint[1],
                                x2=systemTwoCoords["center_x"] + systemTwoOffsetPoint[0],
                                y2=systemTwoCoords["center_y"] + systemTwoOffsetPoint[1],
                                visibility="hidden",
                                style="stroke:#{0}".format(jbColor))
            line["stroke-width"] = 2
            line["class"] = ["jumpbridge", ]
            if "<" in connection:
                line["marker-start"] = "url(#arrowstart_{0})".format(jbColor)
            if ">" in connection:
                line["marker-end"] = "url(#arrowend_{0})".format(jbColor)
            jumps.insert(0, line)

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
        # self.debugWriteSoup()
        return newStatus

    def debugWriteSoup(self):
        svgData = self.soup.prettify("utf-8")
        try:
            with open("/Users/mark/Desktop/output.svg", "wb") as svgFile:
                svgFile.write(svgData)
                svgFile.close()
        except Exception as e:
            LOGGER.error(e)
