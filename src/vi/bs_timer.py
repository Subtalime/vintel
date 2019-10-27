from bs4 import CData, BeautifulSoup
from PyQt5 import QtWidgets, QtWebEngineWidgets
from PyQt5.QtCore import QEvent, pyqtSignal, QObject
import os, time, math, logging
from vi.dotlan_mdoule import Map, System, states


class TestPage(QtWebEngineWidgets.QWebEngineView):
    mouse_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super(TestPage, self).__init__(parent)
        self.installEventFilter(self)
        # self.installEventFilter(self)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        print(event.type(), source)
        if event.type() == QEvent.ShortcutOverride:
            self.mouse_pressed.emit()

        return super().eventFilter(source, event)

    def loadPage(self, content):
        if self.size().isNull():
            self.resize(640, 480)
        self.setHtml(content)


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
            var startTime = new Date().getTime();
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
                                
                secondline.textContent = minutes + ":" + seconds + " " + state;
                if (state == STATE[2]) {
                    var secondsUntilWhite = 3 * 60;
                    var calcValue = Math.round(time / (secondsUntilWhite / 255));
                    if (calcValue > 255) {
                        calcValue = 255;
                        secondline.style = "fill: #008100;";
                    } 
                    secondline.textContent = secondline.textContent + "(" + calcValue + ", " + fullcolorhex(calcValue, 255, calcValue) +")";
                    rect.style.backgroundColor = '#'+fullcolorhex(calcValue, 255, calcValue);
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
        return content
        # return super(MyMap, self).svg

    def __init__(self, region: str = None, testFile=None):
        if not testFile:
            path, file = os.path.split(os.path.abspath(__file__))
            testFile = os.path.join(path, "delve.svg")
            region = "Delve"
        self.testFile = testFile
        self.region = region
        try:
            with open(self.testFile, "r") as f:
                self.svgData = f.read()
        except Exception as e:
            print(e)
            return None
        super(MyMap, self).__init__(region, self.svgData)
        # self.mySystems = {}
        for key in self.systems:
            sys = self.systems[key]
            self.systems[key] = MySystem(sys.name, sys.svgElement, sys.mapSoup,
                                         sys.mapCoordinates, sys.transform, sys.systemId)
        # add the Time-JS
        self.addTimerJs()

    def debugWriteSoup(self):
        svgData = BeautifulSoup(self.svg, 'html.parser').prettify("utf-8")
        dir, file = os.path.split(os.path.abspath(__file__))
        try:
            with open(os.path.join(dir, "output.svg"), "wb") as svgFile:
                svgFile.write(svgData)
        except Exception as e:
            logging.error(e)


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
        if self.status in (states.CLEAR, states.UNKNOWN):
            self.setStatusTime = None
        if self.setStatusTime:
            offset = 0
            if self.status == states.ALARM:
                alarmTime = time.time() - self.lastAlarmTime
                for maxDiff, alarmColor, secondLineColor in self.ALARM_COLORS:
                    if alarmTime < maxDiff:
                        break
                    offset += 1

            # calc the new timer for injecting into JS
            diff = time.time() - self.setStatusTime
            minutes = int(math.floor(diff / 60))
            seconds = int(diff - minutes * 60)
            ndiff = minutes * 60 + seconds
            self.onload = "showTimer({0}, document.querySelector('#{1}'), document.querySelector('#{2}'), '{3}', {4});".format(
                ndiff, self.secondLine["id"], self.rectId, self.status, offset)
            # self.onload = "startTimer({1}, document.querySelector('#{0}'), document.querySelector('#{2}'));".format(
            #     self.secondLine["id"], ndiff, self.rectId)
            self.secondLine.string = "here comes the time"
        elif self.status == states.UNKNOWN:
            self.secondLine.string = "??"
            self.onload = None

class MainApp:

    def __init__(self):
        self.webPage = TestPage()
        self.webPage.mouse_pressed.connect(self.updateMapView)
        self.map = MyMap()
        self.webPage.loadPage(self.map.svg)

    def updateMapView(self):
        system = self.map.systems['Y5C-YD']
        if system.status == states.UNKNOWN:
            system.setStatus(states.ALARM)
        elif system.status == states.ALARM:
            system.setStatus(states.CLEAR)
        elif system.status == states.CLEAR:
            system.setStatus(states.UNKNOWN)
        try:
            self.webPage.loadPage(self.map.svg)
            self.map.debugWriteSoup()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    import sys


    app = QtWidgets.QApplication(sys.argv)
    mainapp = MainApp()
    mainapp.webPage.show()
    mainapp.webPage.raise_()
    app.exec()
