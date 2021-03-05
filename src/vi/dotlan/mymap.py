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

from bs4.element import CData, Tag, ResultSet
from bs4 import BeautifulSoup


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QProgressDialog
from vi.cache import Cache
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.jumpbridge.jumpbridge import JumpBridge, Bridge
from vi.dotlan.system import MySystem
from vi.dotlan.exception import DotlanException
from vi.esi import EsiInterface
from vi.stopwatch.mystopwatch import ViStopwatch
from vi.resources import get_vintel_map_file_path
from vi.states import State
from vi.dotlan.soups import SoupSystem, SoupUse, SoupRect
import requests


class MapDataException(Exception):
    pass


class MapNotInCacheException(MapDataException):
    pass


class MapFileNotFoundException(MapDataException):
    pass


class MapNotFoundOnDotlanException(MapDataException):
    pass


class MapData:
    """get the SVG content from wherever it resides.
    """

    DOTLAN_BASE_URL = u"http://evemaps.dotlan.net/svg/{0}.svg"

    def __init__(self, region: str):
        self.region = region.lower()
        self.svg = None

    def _get_svg_from_dotlan(self):
        url = self.DOTLAN_BASE_URL.format(self.region)
        try:
            content = requests.get(url).text
            if content.startswith("region not found"):
                raise MapNotFoundOnDotlanException(f"Region '{self.region}' could not "
                                                   f"be found on Dotlan ({self.DOTLAN_BASE_URL})")
        except Exception as e:
            raise DotlanException(e)
        return content

    def _from_dotlan(self):
        try:
            self.svg = self._get_svg_from_dotlan()
        except Exception:
            raise

        Cache().put(
            key="map_" + self.region,
            value=self.svg,
            max_age=EsiInterface().secondsTillDowntime() + 3600,
        )

    def _fix_svg(self):
        # replace the header to show encoding
        self.svg = re.sub(
            r"<\?xml.*\?>", r'<?xml version="1.0" encoding="ISO-8859-1"?>', self.svg,
        )

    def _from_cache(self):
        self.svg = Cache().fetch("map_" + self.region)
        if not self.svg:
            raise MapNotInCacheException(f"Region '{self.region}' not found in Cache under 'map_{self.region}'")

    def _from_file(self):
        file_path = get_vintel_map_file_path(region_name=self.region)
        try:
            with open(file_path, "r") as f:
                self.svg = f.read()
        except FileNotFoundError:
            raise MapFileNotFoundException(f"File '{file_path}' does not exist")
        except Exception:
            raise

    def load(self):
        # try in sequence
        try:
            self._from_cache()
        except MapDataException:
            try:
                self._from_file()
            except MapDataException:
                try:
                    self._from_dotlan()
                except DotlanException as e:
                    t = (
                        "No Map in cache, nothing from dotlan. Must give up "
                        "because this happened:\n{0} {1}\n\nThis could be a "
                        "temporary problem (like dotlan is not reachable), or "
                        "everything went to hell. Sorry. This makes no sense "
                        "without the map.".format(type(e), e)
                    )
                    raise DotlanException(t)
        self._fix_svg()
        return self.svg

class MyMap:
    region = None
    parent = None
    progress = None
    sw = ViStopwatch()
    system_updates = 0
    soup = None
    systems = {}
    jumpbridges_loaded = []
    _jumpMapsVisible = False
    _statisticsVisible = False

    def __init__(self, parent=None, region="Delve"):
        self.LOGGER = logging.getLogger(__name__)
        self.parent = parent
        self.region = region

    def load_region(self, region: str = None):
        if not region and not self.region:
            self.LOGGER.error("Trying to load a map with no Region passed")
            return
        if region:
            self.region = region
        self.LOGGER.debug("Loading map for Region: '%s'", self.region)
        if self.parent:
            if not self.progress:
                self.progress = QtWidgets.QProgressDialog(
                    "Loading map data...", "", 0, 1, self.parent
                )
                self.progress.setModal(False)

        svg = MapData(self.region).load()
        # Create soup from the svg
        self.soup = BeautifulSoup(svg, "html.parser")
        # self.soup.findNext('use', {'id': 'id_value'}).findAll('a')
        self._extract_system_from_soup()
        self.systemsById = {}
        for system in self.systems.values():
            self.systemsById[system.system_id] = system
        with self.sw.timer("Prepare SVG"):
            self._prepare_svg()
            self._connect_neighbours()
        self.LOGGER.debug(self.sw.get_report())
        self.marker = self.soup.findAll("g", {"id": "select_marker"})[0]
        # self.marker = self.soup.select("#select_marker")[0]
        self.LOGGER.debug("Map loading for Region '%s': Done", region)
        if self.progress:
            # this closes...
            self.progress.setValue(1)
            self.progress = None

    def _extract_system_from_soup(self):
        uses = {}
        # there will always be the matching "use" for each "symbol"
        with self.sw.timer("extract systems from soup"):
            with self.sw.timer("Soup-Use"):
                # for use in self.soup.select("use"):
                for use in self.soup.findAll("use"):
                    map_use = SoupRect(use)
                    uses[map_use.id] = map_use
            with self.sw.timer("Soup-System"):
                # for symbol in self.soup.select("symbol"):
                for symbol in self.soup.findAll("symbol"):
                    map_symbol = SoupSystem(symbol)
                    if map_symbol.valid:
                        map_symbol.coordinates = uses[map_symbol.symbol_id]
                        self.systems[map_symbol.name] = MySystem(map_symbol,
                                                                 self.soup,
                                                                 )
        self.LOGGER.debug(self.sw.get_report())

    @staticmethod
    def _jump_bridge_markers() -> Tag:
        bs = BeautifulSoup()
        jump_group = bs.new_tag("g", {"id": "jump_bridge_markers"})
        for jbColor in JumpBridge.JB_COLORS:
            start_marker = bs.new_tag(
                "marker",
                # viewBox="0 0 10 10",
                viewBox="0 0 20 20",
                id="arrowstart_{0}".format(jbColor.strip("#")),
                markerUnits="strokeWidth",
                markerWidth="20",
                markerHeight="15",
                refx="-15",
                refy="5",
                orient="auto",
                style="stroke:{0};fill:{0}".format(jbColor),
            )
            start_marker.append(bs.new_tag("path", d="M 10 0 L 10 10 L 0 5 z"))
            jump_group.append(start_marker)
            endmarker = bs.new_tag(
                "marker",
                viewBox="0 0 20 20",
                id="arrowend_{0}".format(jbColor.strip("#")),
                markerUnits="strokeWidth",
                markerWidth="20",
                markerHeight="15",
                refx="25",
                refy="5",
                orient="auto",
                style="stroke:{0};fill:{0}".format(jbColor),
            )
            endmarker.append(bs.new_tag("path", d="M 0 0 L 10 5 L 0 10 z"))
            jump_group.append(endmarker)
        return jump_group

    def _prepare_svg(self):
        try:
            svg = self.soup.findAll("svg")[0]
        except Exception:
            raise MapDataException("SVG Tag not found in soup")
        # Disable dotlan mouse functionality and make all jump lines black
        svg["onmousedown"] = "return false;"
        # make room for the Statistics on the bottom systems
        svg["height"] = int(svg["height"]) + 10

        # update the line color in the connection lines
        jumps = self.soup.findAll("g", {"id": "jumps"})
        if jumps:
            for line in jumps[0].findAll("line"): # self.soup.select("line"):
                line["class"] = "j"

        # Create some new data for the SVG
        # Current system marker ellipse
        group = self.soup.new_tag(
            "g",
            id="select_marker",
            opacity="0",
            activated="0",
            transform="translate(0, 0)",
        )
        # group.append(self.soup.new_tag(
        #     "ellipse", cx="0", cy="0", rx="56", ry="28", style="fill:#462CFF"
        # ))

        # The giant cross-hairs
        for coord in ((0, -10000), (-10000, 0), (10000, 0), (0, 10000)):
            line = self.soup.new_tag(
                "line", x1=coord[0], y1=coord[1], x2="0", y2="0", style="stroke:#462CFF"
            )
            group.append(line)
        svg.insert(0, group)

        # Create jumpbridge markers in a variety of colors
        svg.insert(0, self._jump_bridge_markers())
        try:
            jumps = self.soup.findAll("g", {"id": "jumps"})[0]
        except KeyError:
            raise MapDataException("Could not find #jump tag")

        # Set up the tags for system statistics
        for system_id, system in self.systemsById.items():
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
                transform=f"transform({system.transform[0]},{system.transform[1]})",
            )
            svgtext["id"] = f"stats_{system_id}"
            svgtext["class"] = [
                "statistics",
            ]
            svgtext.string = text
            jumps.append(svgtext)

    def _connect_neighbours(self):
        """
            This will find all neighbours of the systems and connect them.
            It takes a look at all the jumps on the map and gets the system under
            which the line ends
        """
        for jump in self.soup.findAll("g", {"id": "jumps"})[0].findAll("line", {"class": "j"}):
            try:
                (ident, start, end) = jump["id"].split("-")
            except ValueError:
                continue
            if ident == "j":
                start_system = self.systemsById[int(start)]
                stop_system = self.systemsById[int(end)]
                start_system.add_neighbour(stop_system)
                stop_system.add_neighbour(start_system)

    def add_system_statistics(self, statistics):
        self.LOGGER.info("addSystemStatistics start")
        if statistics is not None:
            for system_id, system in self.systemsById.items():
                if system_id in statistics:
                    system.set_statistics(statistics[system_id])
        else:
            for system in self.systemsById.values():
                system.set_statistics(None)
        self.LOGGER.info("addSystemStatistics complete")

    def set_statistics_visibility(self, visible: bool):
        value = "visible" if visible else "hidden"
        # for line in self.soup.select(".statistics"):
        for line in self.soup.findAll("text", {"class": "statistics"}):
            line["visibility"] = value
        self._statisticsVisible = visible

    def set_jump_bridges_visibility(self, visible: bool):
        if len(self.jumpbridges_loaded) == 0:
            return
        value = "visible" if visible else "hidden"
        # for line in self.soup.select(".jumpbridge"):
        for line in self.soup.findAll(Bridge.soup_name, {"class": Bridge.class_name}):
            line["visibility"] = value
        self._jumpMapsVisible = visible

    def add_timer_javascript(self):
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

    @staticmethod
    def timerload(timerload):
        return (
            "showTimer({0}, '{1}', document.querySelector('#{2}'), "
            "document.querySelector('#{3}'), document.querySelector('#{4}'));".format(
                timerload[0], timerload[1], timerload[2], timerload[3], timerload[4],
            )
        )

    @property
    def svg(self):
        # time this complete block
        with self.sw.timer("Building SVG from memory"):
            with self.sw.timer("add Timer JS"):
                self.add_timer_javascript()
            # Re-render all systems
            with self.sw.timer("System update"):
                onload = []
                count = 0
                cjs = ColorJavaScript()
                for system in self.systems.values():
                    if (
                            len(system.timerload) and system.timerload[0] >= 60 * 60 * 2
                    ):  # remove timers older than 2 hours
                        system.set_status(State["UNKNOWN"])
                    # TODO: when changing System, rescan all Chats and update markers that way
                    if system.update(cjs):
                        count += 1
                        if str(system.second_line.string).startswith("-"):
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
                    self.debug_write_soup(content)
        self.time_report(f"\tNumber of timers in SVG: {self.system_updates}")
        return content

    def debug_write_soup(self, svg_data):
        # svgData = BeautifulSoup(self.svg, 'html.parser').prettify("utf-8")
        from vi.resources import get_vintel_log_directory

        ts = datetime.datetime.fromtimestamp(time.time()).strftime("%H_%M_%S")
        try:
            with open(
                    os.path.join(get_vintel_log_directory(), "zoutput_{}.svg".format(ts)), "w+"
            ) as svgFile:
                svgFile.write(svg_data)
        except Exception as e:
            self.LOGGER.error(e)

    def set_jump_bridges(self, jumpbridge_data: list, parent=None):
        """
            Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        if not jumpbridge_data or not isinstance(jumpbridge_data, list) or len(jumpbridge_data) <= 0:
            return
        if self.jumpbridges_loaded == jumpbridge_data:
            return
        jb_builder = JumpBridge(self.systems, self.soup, jumpbridge_data)
        progress = QProgressDialog(
            "Creating Jump-Bridge mappings...", "Abort", 0, len(jumpbridge_data), parent
        )
        progress.setWindowTitle("Jump-Bridge")
        progress.setModal(True)
        progress.setAutoClose(True)
        progress.setValue(0)
        progress.show()
        self.LOGGER.debug("Start building Jump-Bridges")
        for index in jb_builder.build():
            if not index % 4:
                progress.setValue(index)
            if progress.wasCanceled():
                jb_builder.clear()
                break
        progress.setValue(len(jumpbridge_data))
        self.jumpbridges_loaded = jumpbridge_data
        self.LOGGER.debug("Finished building Jump-Bridges")
        del progress


class MyNewMap(MyMap):
    def __init__(self, parent=None, region="Delve"):
        super(MyNewMap, self).__init__(parent, region)


if __name__ == "__main__":
    data = MyNewMap()
    data.load_region()
    print(len(data.svg))
    sw = ViStopwatch()
    iter = 0
    with sw.timer("findAll 'rect' of Class 'o' and Delete them"):
        # for g in data.soup.findAll("g", {"id": "controls"}):
        for g in data.soup.findAll("rect", {"class": "o"}):
            # print(f"{iter}: {g}")
            g.decompose()
            iter += 1
    print(sw.get_report(f"Iterations: {iter}"))

    iter = 0
    with sw.timer("findAll 'a' of Class 'sys' in 'symbol'"):
        for g in data.soup.findAll("symbol"):
            ele = g.findAll("a", {"class": "sys"})
            # print(f"{iter}: {ele}")
            iter += 1
    print(sw.get_report(f"Iterations: {iter}"))

    iter = 0
    with sw.timer("select Class '.sys'"):
        for g in data.soup.select("symbol"):
            ele = g.select(".sys")
            # print(f"{iter}: {ele}")
            iter += 1
    print(sw.get_report(f"Iterations: {iter}"))

    #get first system
    sys = list(data.systems.items())[0]
    print(sys[1])

