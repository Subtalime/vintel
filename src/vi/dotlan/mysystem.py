from vi.dotlan.system import System
import time, math
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

