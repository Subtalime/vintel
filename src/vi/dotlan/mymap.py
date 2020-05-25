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
from vi.states import State
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.dotlan.jumpbridge import Jumpbridge
import re
import sys
import time
import logging
import os
import datetime
from vi.logger.mystopwatch import ViStopwatch


class MyMap(Map):

    def addTimerJs(self):
        realtime_js = ColorJavaScript().js_color_all()
        realtime_js += ColorJavaScript().show_timer()
        js = self.soup.find("script", attrs={"id": "timer", "type": "text/javascript"})
        if not js:
            js = self.soup.new_tag("script", attrs={"id": "timer", "type": "text/javascript"})
        js.string = CData(realtime_js)
        # js.string = realtime_js
        self.soup.svg.append(js)

    def time_report(self, extra_msg: str = None):
        self.LOGGER.debug(self.sw.get_report(extra_msg))

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
                    if len(system.timerload) and system.timerload[0] >= 60 * 60 * 2:  # remove timers older than 2 hours
                        system.setStatus(State['UNKNOWN'])
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
        self.time_report("\tNumber of timers in SVG: %d" % self.system_updates)
        return content

    def __init__(self, parent=None):
        self.progress = None
        self.parent = parent
        self.region = None
        self.sw = ViStopwatch()
        self.system_updates = 0
        self.LOGGER = logging.getLogger(__name__)

    def loadMap(self, region_name):
        testFile = getVintelMap(regionName=region_name)
        self.region = region_name
        try:
            with open(testFile, "r") as f:
                self.svgData = f.read()
            # replace the header to show UTF-8
            self.svgData = re.sub(r"<\?xml.*\?>", r'<?xml version="1.0" encoding="ISO-8859-1"?>', self.svgData)

        except FileNotFoundError as e:
            self.svgData = None
            pass
        if self.parent:
            if not self.progress:
                self.progress = QtWidgets.QProgressDialog("Loading map data...", None, 0, 1, self.parent)
                self.progress.setModal(False)

        super(MyMap, self).__init__(region_name, self.svgData)
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

    def setJumpbridges(self, jumpbridgesData, parent = None):
        """
            Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        if not jumpbridgesData or len(jumpbridgesData) <= 0:
            return
        jb = Jumpbridge(self.systems, self.soup, jumpbridgesData)
        progress = QtWidgets.QProgressDialog("Creating Jump-Bridge mappings...", "Abort", 0, len(jumpbridgesData),
                                             parent)
        progress.setWindowTitle("Jump-Bridge")
        progress.setModal(True)
        progress.setValue(0)
        jumps = 0
        for data, loc in jb.build():
            jumps += 1
            if not jumps % 4:
                progress.setValue(jumps)
            if progress.wasCanceled():
                break
        progress.setValue(len(jumpbridgesData))
