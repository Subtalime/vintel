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

JB_COLORS = ("800000", "808000", "BC8F8F", "ff00ff", "c83737", "FF6347", "917c6f", "ffcc00",
             "88aa00" "FFE4E1", "008080", "00BFFF", "4682B4", "00FF7F", "7FFF00", "ff6600",
             "CD5C5C", "FFD700", "66CDAA", "AFEEEE", "5F9EA0", "FFDEAD", "696969", "2F4F4F")
LOGGER = logging.getLogger(__name__)


class MyMap(Map):

    def addTimerJs(self):
        realtime_js = """
        // courtesy of https://github.com/PimpTrizkit/PJs 
        const pSBC=(p,c0,c1,l)=>{
            let r,g,b,P,f,t,h,i=parseInt,m=Math.round,a=typeof(c1)=="string";
            if(typeof(p)!="number"||p<-1||p>1||typeof(c0)!="string"||(c0[0]!='r'&&c0[0]!='#')||(c1&&!a))return null;
            if(!this.pSBCr)this.pSBCr=(d)=>{
                let n=d.length,x={};
                if(n>9){
                    [r,g,b,a]=d=d.split(","),n=d.length;
                    if(n<3||n>4)return null;
                    x.r=i(r[3]=="a"?r.slice(5):r.slice(4)),x.g=i(g),x.b=i(b),x.a=a?parseFloat(a):-1
                }else{
                    if(n==8||n==6||n<4)return null;
                    if(n<6)d="#"+d[1]+d[1]+d[2]+d[2]+d[3]+d[3]+(n>4?d[4]+d[4]:"");
                    d=i(d.slice(1),16);
                    if(n==9||n==5)x.r=d>>24&255,x.g=d>>16&255,x.b=d>>8&255,x.a=m((d&255)/0.255)/1000;
                    else x.r=d>>16,x.g=d>>8&255,x.b=d&255,x.a=-1
                }return x};
            h=c0.length>9,h=a?c1.length>9?true:c1=="c"?!h:false:h,f=pSBCr(c0),P=p<0,t=c1&&c1!="c"?pSBCr(c1):P?{r:0,g:0,b:0,a:-1}:{r:255,g:255,b:255,a:-1},p=P?p*-1:p,P=1-p;
            if(!f||!t)return null;
            if(l)r=m(P*f.r+p*t.r),g=m(P*f.g+p*t.g),b=m(P*f.b+p*t.b);
            else r=m((P*f.r**2+p*t.r**2)**0.5),g=m((P*f.g**2+p*t.g**2)**0.5),b=m((P*f.b**2+p*t.b**2)**0.5);
            a=f.a,t=t.a,f=a>=0||t>=0,a=f?a<0?t:t<0?a:a*P+t*p:0;
            if(h)return"rgb"+(f?"a(":"(")+r+","+g+","+b+(f?","+m(a*1000)/1000:"")+")";
            else return"#"+(4294967296+r*16777216+g*65536+b*256+(f?m(a*255):0)).toString(16).slice(1,f?undefined:-2)
        }

        // max time for alarm, rect color, secondLine color [ array in set of 3 ]
        """
        realtime_js += ColorJavaScript().getJs()
        realtime_js += """
        var UNKNOWN_COLOR = "#FFFFFF";
        var CLEAR_COLOR = "#59FF6C";
        var STATE = ['alarm', 'was alarmed', 'clear', 'unknown', 'ignore', 'no change', 'request', 'location'];
        // seconds since a state has been announced, state, text-line to place text, Rectangle, Ice-Rectangle
        function showTimer(currentTime, state, secondline, rect, rectice) {
            var bgcolor = UNKNOWN_COLOR; // the default
            var endcolor = CLEAR_COLOR;
            var slcolor = '#000000';
            var arrayoffset = -1;
            var maxtime = 0;
            var startTime = new Date().getTime() - currentTime * 1000;
            window.setInterval(function() {
                var time = new Date().getTime() - startTime;
                var elapsed = Math.ceil(time / 100) / 10;
                if (elapsed >= maxtime) {
                    if (state == STATE[0]) { // Alarm
                        while (arrayoffset + 1 < ALARM_COLORS.length / 3 && elapsed > maxtime) {
                            arrayoffset += 1;
                            bgcolor = endcolor =  ALARM_COLORS[arrayoffset * 3 + 1];
                            if (arrayoffset + 1 < ALARM_COLORS.length / 3) {
                                endcolor = ALARM_COLORS[(arrayoffset + 1) * 3 + 1];
                            }
                            slcolor = ALARM_COLORS[arrayoffset * 3 + 2];
                            maxtime = ALARM_COLORS[arrayoffset * 3];
                        }
                    }
                    else if (state == STATE[2]) { // Clear
                        while (arrayoffset + 1 < CLEAR_COLORS.length / 3 && elapsed > maxtime) {
                            arrayoffset += 1;
                            bgcolor = endcolor = CLEAR_COLORS[arrayoffset * 3 + 1];
                            if (arrayoffset + 1 < CLEAR_COLORS.length / 3) {
                                endcolor = CLEAR_COLORS[(arrayoffset + 1) * 3 + 1];
                            }
                            slcolor = CLEAR_COLORS[arrayoffset * 3 + 2];
                            maxtime = CLEAR_COLORS[arrayoffset * 3];
                        }
                    }
                    else if (state == STATE[6]) { // Request
                        while (arrayoffset + 1 < REQUEST_COLORS.length / 3 && elapsed > maxtime) {
                            arrayoffset += 1;
                            bgcolor = endcolor = REQUEST_COLORS[arrayoffset * 3 + 1];
                            if (arrayoffset + 1 < REQUEST_COLORS.length / 3) {
                                endcolor = REQUEST_COLORS[(arrayoffset + 1) * 3 + 1];
                            }
                            slcolor = REQUEST_COLORS[arrayoffset * 3 + 2];
                            maxtime = REQUEST_COLORS[arrayoffset * 3];
                        }
                    }
                }
                var minutes = parseInt(elapsed / 60, 10);
                var seconds = parseInt(elapsed % 60, 10);
                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;
                secondline.setAttribute("style", "fill: " + slcolor);
                var achieved = 0;
                if (arrayoffset >= 0) {
                    achieved = elapsed / maxtime;
                }
                var newcolor = pSBC(achieved, bgcolor, endcolor, 1);
                rect.setAttribute('style', "fill: " + newcolor);
                rectice.setAttribute('style', "fill: " + newcolor);
                secondline.textContent = minutes + ":" + seconds;
            }, 1000);
        }
        """

        js = self.soup.find("script", attrs={"id": "timer", "type": "text/javascript"})
        if not js:
            js = self.soup.new_tag("script", attrs={"id": "timer", "type": "text/javascript"})
        js.string = CData(realtime_js)
        self.soup.svg.append(js)

    @property
    def svg(self):
        LOGGER.debug("Start SVG {}".format(datetime.datetime.now()))
        self.addTimerJs()
        # Re-render all systems
        onload = []
        # for system in self.mySystems.values():
        for system in self.systems.values():
            if len(system.timerload) and system.timerload[0] >= 60 * 60 * 2:  # remove timers older than 2 hours
                system.setStatus(states.UNKNOWN)
            system.update()
            if len(system.timerload):  # remove timers older than 2 hours
                onload.append(
                    "showTimer({0}, '{1}', document.querySelector('#{2}'), document.querySelector('#{3}'), document.querySelector('#{4}'));".format(
                        system.timerload[0], system.timerload[1], system.timerload[2], system.timerload[3],
                        system.timerload[4]))
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
        LOGGER.debug("End SVG {}".format(datetime.datetime.now()))
        if not getattr(sys, 'frozen', False):
            self.debugWriteSoup(content)
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
            LOGGER.error(e)

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
