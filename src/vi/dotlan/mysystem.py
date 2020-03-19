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

from vi.dotlan.system import System
import time
import datetime
import math
from vi import states
from vi.dotlan.colorjavascript import ColorJavaScript
import logging


class MySystem(System):
    def __init__(self, name, svgElement, mapSoup, mapCoordinates, transform, systemId):
        super(MySystem, self).__init__(name, svgElement, mapSoup, mapCoordinates, transform,
                                       systemId)
        self.timerload = ()
        self.name_label = self.name.replace("-", "_").lower()
        self.rectId = self.svgElement.select("rect")[0]["id"]
        if len(self.svgElement.select("rect")) > 1:
            self.rectIce = self.svgElement.select("rect")[1]
        else:
            self.rectIce = self.rect
        if not self.rectIce.has_attr("id"):
            self.rectIce["id"] = "icerect{}".format(self.name_label)
        self.rectIdIce = self.rectIce["id"]
        if not self.secondLine.has_attr("id"):
            self.secondLine["id"] = "watch{}".format(self.name_label)
        # set default to White
        for rect in self.svgElement.select("rect"):
            rect["style"] = "fill: #ffffff"

    def setStatus(self, new_status, alarm_time: float = time.time()):
        super(MySystem, self).setStatus(new_status, alarm_time)

    def update(self, cjs: ColorJavaScript):
        updated = False
        # calc the new timer for injecting into JS
        diff = max(0, math.floor(time.time() - self.lastAlarmTime))
        # diff = time.time() - self.lastAlarmTime
        minutes = int(math.floor(diff / 60))
        seconds = int(diff - minutes * 60)
        ndiff = int(minutes * 60 + seconds)
        # if self.status != states.UNKNOWN and (diff < 0 or ndiff > cjs.max_time(self.status)):  # anything older than max color-size
        #     self.setStatus(states.UNKNOWN)
        if self.status != states.UNKNOWN:
            self.secondLine.string = "{m:02d}:{s:02d}".format(m=minutes, s=seconds)
            self.timerload = (ndiff, self.status, self.secondLine["id"], self.rectId, self.rectIdIce)
            color, text_color = cjs.color_at(ndiff, self.status)
            updated = True
            for rect in self.svgElement.select("rect"):
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
            self.name, self.lastAlarmTime, la, time.time(), no, time.time() - self.lastAlarmTime,
            (",".join("{}.{}".format(key, val) for key, val in self.statistics.items())),)
        return ret_str
