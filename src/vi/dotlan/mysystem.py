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
            # if rect.has_attr("style"):
            rect["style"] = "fill: #ffffff"

    def setStatus(self, newStatus):
        super(MySystem, self).setStatus(newStatus)
        self.setStatusTime = time.time()

    def update(self):
        # super(MySystem, self).update()
        if self.status != states.UNKNOWN:
            # calc the new timer for injecting into JS
            diff = time.time() - self.lastAlarmTime
            minutes = int(math.floor(diff / 60))
            seconds = int(diff - minutes * 60)
            ndiff = minutes * 60 + seconds
            self.timerload = (ndiff, self.status, self.secondLine["id"], self.rectId, self.rectIdIce)
        else:
            self.secondLine.string = "??"
            self.timerload = ()
