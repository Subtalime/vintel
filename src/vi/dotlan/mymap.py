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

from bs4.element import CData
from PyQt5 import QtWidgets
from vi.dotlan.map import Map
from vi.resources import getVintelMap
from vi import states
from vi.dotlan.colorjavascript import ColorJavaScript
import sys
import time
import logging
import math
import os
import datetime
from vi.logger.mystopwatch import ViStopwatch


JB_COLORS = ("800000", "808000", "BC8F8F", "ff00ff", "c83737", "FF6347", "917c6f", "ffcc00",
             "88aa00" "FFE4E1", "008080", "00BFFF", "4682B4", "00FF7F", "7FFF00", "ff6600",
             "CD5C5C", "FFD700", "66CDAA", "AFEEEE", "5F9EA0", "FFDEAD", "696969", "2F4F4F")


class MyMap(Map):

    def addTimerJs(self):
        self.LOGGER.debug(" Start addTimerJs")
        realtime_js = ColorJavaScript().js_color_all()
        realtime_js += ColorJavaScript().show_timer()
        js = self.soup.find("script", attrs={"id": "timer", "type": "text/javascript"})
        if not js:
            js = self.soup.new_tag("script", attrs={"id": "timer", "type": "text/javascript"})
        js.string = CData(realtime_js)
        # js.string = realtime_js
        self.soup.svg.append(js)
        self.LOGGER.debug(" End addTimerJs")

    def time_report(self, extra_msg: str = None):
        self.LOGGER.debug(self.sw.get_report(extra_msg))

    @property
    def svg(self):
        with self.sw.timer("SVG"):
            with self.sw.timer("add Timer JS"):
                self.addTimerJs()
            # Re-render all systems
            with self.sw.timer("System update"):
                onload = []
                count = 0
                cjs = ColorJavaScript()
                for system in self.systems.values():
                    if len(system.timerload) and system.timerload[0] >= 60 * 60 * 2:  # remove timers older than 2 hours
                        system.setStatus(states.UNKNOWN)
                    #TODO: when changing System, rescan all Chats and update markers that way
                    if system.update(cjs):
                        count += 1
                        if str(system.secondLine.string).startswith("-"):
                            self.LOGGER.error(system)
                    if len(system.timerload):  # remove timers older than 2 hours
                        onload.append(
                            "showTimer({0}, '{1}', document.querySelector('#{2}'), document.querySelector('#{3}'), document.querySelector('#{4}'));".format(
                                system.timerload[0], system.timerload[1], system.timerload[2], system.timerload[3],
                                system.timerload[4]))
                self.system_updates = count
            # Update the OnLoad JavaScript in the page
            with self.sw.timer("add window.onload JS"):
                js_onload = self.soup.find("script", attrs={"id": "onload"})
                if not js_onload:
                    js_onload = self.soup.new_tag("script",
                                                  attrs={"id": "onload", "type": "text/javascript"})
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
                    new_value = (1 - (now - float(self.marker["activated"])) / 10)
                    if new_value < 0:
                        new_value = "0"
                    self.marker["opacity"] = new_value
            with self.sw.timer("Build Map Content"):
                content = str(self.soup)
            if not getattr(sys, 'frozen', False):
                with self.sw.timer("Dump Map To disc"):
                    # pass
                    self.debugWriteSoup(content)
        self.time_report("System-Updates: %d" % self.system_updates)
        return content

    def __init__(self, parent=None):
        self.progress = None
        self.parent = parent
        self.region = None
        self.sw = ViStopwatch()
        self.system_updates = 0
        self.LOGGER = logging.getLogger(__name__)

    def loadMap(self, regionName):
        testFile = getVintelMap(regionName=regionName)
        self.region = regionName
        try:
            with open(testFile, "r") as f:
                self.svgData = f.read()
        except FileNotFoundError as e:
            self.svgData = None
            pass
        if self.parent:
            if not self.progress:
                self.progress = QtWidgets.QProgressDialog("Loading map data...", None, 0, 1, self.parent)
                self.progress.setModal(False)

        super(MyMap, self).__init__(regionName, self.svgData)
        # self.addTimerJs()
        if self.parent:
            # this closes...
            self.progress.setValue(1)
            self.progress = None
        return self

    def debugWriteSoup(self, svgData):
        # svgData = BeautifulSoup(self.svg, 'html.parser').prettify("utf-8")
        from vi.resources import getVintelLogDir
        dir, file = os.path.split(os.path.abspath(__file__))
        ts = datetime.datetime.fromtimestamp(time.time()).strftime("%H_%M_%S")
        try:
            with open(os.path.join(getVintelLogDir(), "zoutput_{}.svg".format(ts)), "w+") as svgFile:
                svgFile.write(svgData)
        except Exception as e:
            self.LOGGER.error(e)

    def setJumpbridges(self, parent, jumpbridgesData):
        """
            Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        if not jumpbridgesData or len(jumpbridgesData) <= 0:
            return
        try:
            progress = QtWidgets.QProgressDialog("Creating Jump-Bridge mappings...", "Abort", 0, len(jumpbridgesData),
                                                 parent)
            progress.setWindowTitle("Jump-Bridge")
            progress.setModal(True)
            progress.setValue(0)
            soup = self.soup
            # remove existing Jump-Brdiges
            for bridge in soup.select(".jumpbridge"):
                bridge.decompose()
            jumps = soup.select("#jumps")[0]
            colorCount = 0
            jumpCount = 0
            for bridge in jumpbridgesData:
                jumpCount += 1
                if jumpCount % 4:
                    progress.setValue(jumpCount)
                if progress.wasCanceled():
                    break
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

                # Construct the arc, color it and add it to the jumps
                x1 = systemOneCoords["center_x"] + systemOneOffsetPoint[0]
                y1 = systemOneCoords["center_y"] + systemOneOffsetPoint[1]
                x2 = systemTwoCoords["center_x"] + systemTwoOffsetPoint[0]
                y2 = systemTwoCoords["center_y"] + systemTwoOffsetPoint[1]
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                dx = (x2 - x1) / 2
                dy = (y2 - y1) / 2
                dd = math.sqrt(dx * dx + dy * dy)
                ex = cx + dy / dd * 40
                ey = cy - dx / dd * 40
                line = soup.new_tag("path", d="M{} {}Q{} {} {} {}".format(x1, y1, ex, ey, x2, y2), visibility="hidden",
                                    style="stroke:#{0}; fill: none".format(jbColor))
                line["stroke-width"] = 2
                line["class"] = ["jumpbridge", ]
                if "<" in connection:
                    line["marker-start"] = "url(#arrowstart_{0})".format(jbColor)
                if ">" in connection:
                    line["marker-end"] = "url(#arrowend_{0})".format(jbColor)
                jumps.insert(0, line)
        except Exception:
            raise
        finally:
            if progress:
                # this will close it
                progress.setValue(len(jumpbridgesData))
