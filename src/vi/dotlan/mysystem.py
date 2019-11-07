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
import math
from vi import states


class MySystem(System):
    def __init__(self, name, svgElement, mapSoup, mapCoordinates, transform, systemId):
        super(MySystem, self).__init__(name, svgElement, mapSoup, mapCoordinates, transform,
                                       systemId)
        self.setStatusTime = None
        self.onload = None
        self.rectId = self.svgElement.select("rect")[0]["id"]
        if not self.secondLine.has_attr("id"):
            self.secondLine["id"] = "watch{}".format(self.name)

    def setStatus(self, newStatus):
        super(MySystem, self).setStatus(newStatus)
        self.setStatusTime = time.time()

    def update(self):
        super(MySystem, self).update()
        if self.status != states.UNKNOWN:
            offset = 0
            if self.status == states.ALARM:
                alarmTime = time.time() - self.lastAlarmTime
                for maxDiff, alarmColor, secondLineColor in self.ALARM_COLORS:
                    if alarmTime < maxDiff:
                        break
                    offset += 1

            # calc the new timer for injecting into JS
            diff = time.time() - self.lastAlarmTime
            minutes = int(math.floor(diff / 60))
            seconds = int(diff - minutes * 60)
            ndiff = minutes * 60 + seconds
            self.onload = "showTimer({0}, document.querySelector('#{1}'), document.querySelector('#{2}'), '{3}', {4});".format(
                ndiff, self.secondLine["id"], self.rectId, self.status, offset)
            # self.secondLine.string = "here comes the time"
        elif self.status == states.UNKNOWN:
            self.secondLine.string = "??"
            self.onload = None

