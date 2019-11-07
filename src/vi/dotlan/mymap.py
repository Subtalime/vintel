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

from bs4.element import  CData
from PyQt5 import  QtWidgets
from vi.dotlan.map import Map
from vi.resources import getVintelMap
import time
import logging
import os
import datetime

JB_COLORS = ("800000", "808000", "BC8F8F", "ff00ff", "c83737", "FF6347", "917c6f", "ffcc00",
             "88aa00" "FFE4E1", "008080", "00BFFF", "4682B4", "00FF7F", "7FFF00", "ff6600",
             "CD5C5C", "FFD700", "66CDAA", "AFEEEE", "5F9EA0", "FFDEAD", "696969", "2F4F4F")


class MyMap(Map):

    def addTimerJs(self):
        realtime_js = """
        var rgbToHex = function (rgb) { 
            var hex = Number(rgb).toString(16);
            if (hex.length < 2) {
                hex = "0" + hex;
            }
            return hex;
        };
        var fullColorHex = function(r,g,b) {   
          var red = rgbToHex(r);
          var green = rgbToHex(g);
          var blue = rgbToHex(b);
          return red+green+blue;
        };
        // max time for alarm, rect color, secondLine color
        var ALARM_COLORS = [60 * 4, "#FF0000", "#FFFFFF", 60 * 10, "#FF9B0F", "#FFFFFF", 60 * 15, "#FFFA0F", "#000000",
                        60 * 25, "#FFFDA2", "#000000", 60 * 60 * 24, "#FFFFFF", "#000000"];
        var ALARM_COLOR = ALARM_COLORS[2];
        var UNKNOWN_COLOR = "#FFFFFF";
        var CLEAR_COLOR = "#59FF6C";
        var STATE = ['alarm', 'was alarmed', 'clear', 'unknown', 'ignore', 'no change', 'request', 'location'];
        // seconds to start at, where, fill, current state, alarm_colors offset
        function showTimer(currentTime, secondline, rect, state, arrayoffset) {
            var bgcolor = UNKNOWN_COLOR; // the default
            var slcolor = '#000000';
            var maxtime = 60 * 60 * 24 - currentTime;
            var startTime = new Date().getTime() - currentTime * 1000;
            if (state == STATE[0]) { // Alarm
                bgcolor = ALARM_COLORS[arrayoffset + 1];
                slcolor = ALARM_COLORS[arrayoffset + 2];
                maxtime = ALARM_COLORS[arrayoffset] - currentTime;
            }
            else if (state == STATE[2]) { // Clear
                bgcolor = CLEAR_COLOR;
            }
            window.setInterval(function() {
                var time = new Date().getTime() - startTime;
                var elapsed = Math.ceil(time / 100) / 10;
                if (elapsed > maxtime) {
                    // work out if there is a new color in alarm_colors
                    return; 
                }
                minutes = parseInt(elapsed / 60, 10);
                seconds = parseInt(elapsed % 60, 10);

                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;

                secondline.textContent = minutes + ":" + seconds;
                if (state == STATE[2]) {
                    var secondsUntilWhite = 3 * 60;
                    var calcValue = Math.round(time / (secondsUntilWhite / 255));
                    if (calcValue > 255) {
                        calcValue = 255;
                        secondline.style = "fill: #008100;";
                    } 
//                    secondline.textContent = secondline.textContent + "(" + calcValue + ", " + fullcolorhex(calcValue, 255, calcValue) +")";
                    rect.style.backgroundColor = '#'+fullColorHex(calcValue, 255, calcValue);
                }
                else { 
                    secondline.style.color = slcolor;
                    rect.style.backgroundColor = bgcolor;
                }

            }, 1000);

        }
        function startTimerCountdown(seconds, display, frame) {
            var start = new Date().getTime() + seconds * 1000, elapsed = 0;
            window.setInterval(function() {
                var time = start - new Date().getTime();
                elapsed = Math.ceil(time / 100) / 10;

                if (elapsed < 0) {
                    return;
                }
                minutes = parseInt(elapsed / 60, 10);
                seconds = parseInt(elapsed % 60, 10);

                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;

                display.textContent = minutes + ":" + seconds;
            }, 1000);
        }
        function startTimer(secondsMax, display, frame) {
            var end = new Date().getTime() + secondsMax * 1000, elapsed = 0, start = new Date().getTime();
            window.setInterval(function() {
                var time = new Date().getTime();
                elapsed = Math.ceil((end - time) / 100) / 10;

                if (elapsed < 0) {
                    return;
                }
                elapsed = (time - start) / 1000;
                minutes = parseInt(elapsed / 60, 10);
                seconds = parseInt(elapsed % 60, 10);

                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;

                display.textContent = minutes + ":" + seconds;
            }, 1000);
        }
        """

        js = self.soup.new_tag("script", attrs={"id": "timer", "type": "text/javascript"})
        js.string = CData(realtime_js)
        self.soup.svg.append(js)

    @property
    def svg(self):
        # Re-render all systems
        onload = []
        # for system in self.mySystems.values():
        for system in self.systems.values():
            system.update()
            if system.onload:
                onload.append(system.onload)
        # Update the marker
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
            startjs += "}\n"
            js_onload.string = startjs

        # Update the marker
        if not self.marker["opacity"] == "0":
            now = time.time()
            newValue = (1 - (now - float(self.marker["activated"])) / 10)
            if newValue < 0:
                newValue = "0"
            self.marker["opacity"] = newValue
        content = str(self.soup)
        # self.debugWriteSoup(content)
        return content

    def __init__(self, parent=None):
        self.progress = None
        self.parent = parent
        self.region = None

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
        self.addTimerJs()
        if self.parent:
            # this closes...
            self.progress.setValue(1)
            self.progress = None
        return self


    def debugWriteSoup(self, svgData):
        # svgData = BeautifulSoup(self.svg, 'html.parser').prettify("utf-8")
        dir, file = os.path.split(os.path.abspath(__file__))
        ts = datetime.datetime.fromtimestamp(time.time()).strftime("%H_%M_%S")
        try:
            with open(os.path.join(dir, "output_{}.svg".format(ts)), "w+") as svgFile:
                svgFile.write(svgData)
        except Exception as e:
            logging.error(e)


    def setJumpbridges(self, parent, jumpbridgesData):
        """
            Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        if not jumpbridgesData or len(jumpbridgesData) <= 0:
            return
        try:
            progress = QtWidgets.QProgressDialog("Creating Jump-Bridge mappings...", "Abort", 0, len(jumpbridgesData), parent)
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
                jumpCount+=1
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

                # Construct the line, color it and add it to the jumps
                line = soup.new_tag("line", x1=systemOneCoords["center_x"] + systemOneOffsetPoint[0],
                                    y1=systemOneCoords["center_y"] + systemOneOffsetPoint[1],
                                    x2=systemTwoCoords["center_x"] + systemTwoOffsetPoint[0],
                                    y2=systemTwoCoords["center_y"] + systemTwoOffsetPoint[1], visibility="hidden",
                                    style="stroke:#{0}".format(jbColor))
                line["stroke-width"] = 2
                line["class"] = ["jumpbridge", ]
                if "<" in connection:
                    line["marker-start"] = "url(#arrowstart_{0})".format(jbColor)
                if ">" in connection:
                    line["marker-end"] = "url(#arrowend_{0})".format(jbColor)
                jumps.insert(0, line)
        except Exception as e:
            raise
        finally:
            if progress:
                # this will close it
                progress.setValue(len(jumpbridgesData))
