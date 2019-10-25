from bs4 import BeautifulSoup, CData
from vi.dotlan.map import Map
import time, logging, os, datetime

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
        self.debugWriteSoup(content)
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
        except FileNotFoundError as e:
            self.svgData = testFile
            pass
        super(MyMap, self).__init__(region, self.svgData)
        # self.mySystems = {}
        # for key in self.systems:
        #     sys = self.systems[key]
        #     self.systems[key] = MySystem(sys.name, sys.svgElement, sys.mapSoup,
        #                                  sys.mapCoordinates, sys.transform, sys.systemId)
        # add the Time-JS
        self.addTimerJs()

    def debugWriteSoup(self, svgData):
        # svgData = BeautifulSoup(self.svg, 'html.parser').prettify("utf-8")
        dir, file = os.path.split(os.path.abspath(__file__))
        ts = datetime.datetime.fromtimestamp(time.time()).strftime("%H_%M_%S")
        try:
            with open(os.path.join(dir, "output_{}.svg".format(ts)), "w+") as svgFile:
                svgFile.write(svgData)
        except Exception as e:
            logging.error(e)
