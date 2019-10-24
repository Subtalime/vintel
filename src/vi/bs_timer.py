from bs4 import BeautifulSoup, CData
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebEngine
import os, time, math
from vi.dotlan import Map, System, states

class TestPage(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super(TestPage, self).__init__(parent)
        self.installEventFilter(self)

    def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
        # print(a1.type(), a0)
        return super().eventFilter(a0, a1)

    def loadPage(self, content):
        if self.size().isNull():
            self.resize(640, 480)
        self.setHtml(content)


class MyMap(Map):

    def addTimerJs(self):
        realtime_js = """
        function startTimerCountdown(seconds, display) {
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
        function startTimer(secondsMax, display) {
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
        for system in self.mySystems.values():
            system.update()
            if system.onload:
                onload.append(system.onload)
        # Update the marker
        js_onload = self.soup.find("script", {"id": "onload"})
        if not js_onload:
            js_onload = self.soup.new_tag("script", attrs={"id": "onload", "type": "text/javascript"})
            self.soup.svg.append(js_onload)
        js_onload = self.soup.find("script", {"id": "onload"})
        if len(onload) > 0:
            startjs = "window.onload = function () {\n"
            for load in onload:
                startjs += load + "\n"
            startjs += "}\n"
            js_onload.string = startjs

        if not self.marker["opacity"] == "0":
            now = time.time()
            newValue = (1 - (now - float(self.marker["activated"])) / 10)
            if newValue < 0:
                newValue = "0"
            self.marker["opacity"] = newValue
        content = str(self.soup)
        return content


    def __init__(self, region: str=None, testFile=None):
        if not testFile:
            path, file = os.path.split(os.path.abspath(__file__))
            testFile = os.path.join(path,"delve.svg")
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
        self.mySystems = {}
        for key in self.systems:
            sys = self.systems[key]
            self.mySystems[key] = MySystem(sys.name, sys.svgElement, sys.mapSoup, sys.mapCoordinates, sys.transform, sys.systemId)
        # add the Time-JS
        self.addTimerJs()

    def do_it(self):
        realtime_js = """
        function startTimerCountdown(seconds, display) {
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
        function startTimer(secondsMax, display) {
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
        colors = """
            var ALARM_COLORS = [(60 * 4, "#FF0000", "#FFFFFF"), (60 * 10, "#FF9B0F", "#FFFFFF"), (60 * 15, "#FFFA0F", "#000000"),
                            (60 * 25, "#FFFDA2", "#000000"), (60 * 60 * 24, "#FFFFFF", "#000000")];
            var ALARM_COLOR = ALARM_COLORS[0][1];
            var UNKNOWN_COLOR = "#FFFFFF";
            var CLEAR_COLOR = "#59FF6C";
        """

        soup = BeautifulSoup(self.svg, features="html.parser")
        header = soup.svg
        body = soup.svg
        style = soup.new_tag("style", attrs={"type": "text/css", "id": "style5"})
        style.string = CData("""
        .stopwatch {
        fill: #ffd39f; 
        stroke-width: 3; 
        stroke: #000000;
        }
        .es	{ font-size: 9px; font-family: Arial, Helvetica, sans-serif; fill: #000000; }
        .er	{ font-weight: bold; font-size: 7px; font-family: verdana, Arial, sans-serif; fill: #000000; }
        """)

        header.append(style)
        output = soup.find("defs")
        # output = soup.find("symbol",{"id": "def30004785"})

        onload = ""
        for i in range(1, 2):
            s = soup.new_tag("symbol", attrs={"id": "def{f:08d}".format(f=i)})
            a = soup.new_tag("a", attrs={"class": "sys", "id": "a{f:08d}".format(f=i), "xlink:href": "http://evemaps.dotlan.net/map/Querious/8QT-H4", "target": "_top"})
            r = soup.new_tag("rect", attrs={"x": 4, "y": i * 8, "width": 100,
                                            "height": 60, "id": "rect{f:08d}".format(f=i),
                                            "class": "e"})
            t = soup.new_tag("text", attrs={"x": 10, "y": i * 8 + 10, "id": "timer{f:08d}".format(f=i), "class": "es", "text-anchor": "middle"})
            t.string="Time{}".format(i)
            st = soup.new_tag("text", attrs={"class": "er", "style": "fill: #000000", "text-anchor": "middle", "x": 14, "y": i * 8 + 27})
            st.string = "?"
            d = soup.new_tag("div", attrs={"id": "timer{f:08d}".format(f=i)})
            # d.append(r)
            a.append(r)
            a.append(t)
            # if a.has_attr("target"):
            #     target = a.get("target")
            #     s["dummy"] = target
            a.append(st)
            s.append(a)
            # print(a)
            output.append(s)
            use = soup.findAll("g", {"id": "sysuse"})
            u = soup.new_tag("use", attrs={"height": 30, "id": "sys{f:08d}".format(f=i), "width": 62.5, "x": 4, "xlink:href": "#def{f:08d}".format(f=i), "y": i*8+16})
            use[0].append(u)
            onload += "var field{n:1} = document.querySelector('#timer{t:08d}');\nvar delay{n:1} = {n:1} * 60;\nstartTimer(delay{n:1}, field{n:1});\n".format(t=i, n=i)
        # defs = body.find("defs")
        # if not defs:
        #     print("no spot to put")
        #     exit(1)
        # defs.append(output)

        startjs = "window.onload = function () {\n"+onload+"\n}"
        js = soup.new_tag("script", attrs={"id": "onload", "type": "text/javascript"})
        js.string = CData(realtime_js)

        header.append(js)
        js = soup.new_tag("script", attrs={"id": "timer", "type": "text/javascript"})
        js.string = startjs
        header.append(js)
        path, file = os.path.split(self.testFile)
        file = file.replace(".", "1.")
        res = os.path.join(os.path.abspath(path), file)
        with open(res, "w") as f:
            f.write(soup.prettify())
        return res

class MySystem(System):
    def __init__(self, name, svgElement, mapSoup, mapCoordinates, transform, systemId):
        super(MySystem, self).__init__(name, svgElement, mapSoup, mapCoordinates, transform, systemId)
        self.setStatusTime = None
        self.onload = None
        if not self.secondLine.has_attr("id"):
            self.secondLine["id"] = "watch{}".format(self.name)

    def setStatus(self, newStatus):
        super(MySystem, self).setStatus(newStatus)
        self.setStatusTime = time.time()

    def update(self):
        super(MySystem, self).update()
        if self.status == states.CLEAR:
            self.setStatusTime = None
        if self.setStatusTime:
            # calc the new timer for injecting into JS
            diff = time.time() - self.setStatusTime
            minutes = int(math.floor(diff / 60))
            seconds = int(diff - minutes * 60)
            ndiff = minutes * 60 + seconds
            self.onload = "startTimer({1}, document.querySelector('#{0}'));".format(self.secondLine["id"], ndiff)
            self.secondLine.string = "here comes the time"




if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    map = MyMap()

    # received = map.do_it()
    systems = map.mySystems

    system = systems['Y5C-YD']
    system.setStatus(states.ALARM)
    page = TestPage()
    page.show()
    # while True:
    page.loadPage(map.svg)
    # time.sleep(3)
    # system.update()
    app.exec()
