from bs4 import BeautifulSoup, CData

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
with open("delve.svg", "r") as f:
# with open("test.html", "r") as f:
    svg = f.read()

soup = BeautifulSoup(svg, features="html.parser")
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
output1 = output.findAll("symbol", {"id": "def30004012"})[0]

onload = ""
for i in range(1, 2):
    s = soup.new_tag("symbol", attrs={"id": "def{f:08d}".format(f=i)})
    a = soup.new_tag("a", attrs={"class": "sys", "id": "a{f:08d}".format(f=i), "xlink:href": "http://evemaps.dotlan.net/map/Querious/8QT-H4", "target": "_top"})
    r = soup.new_tag("rect", attrs={"x": 100, "y": i * 100, "width": 100,
                                    "height": 60, "id": "rect{f:08d}".format(f=i),
                                    "class": "e"})
    t = soup.new_tag("text", attrs={"x": 114, "y": i * 100 + 10, "id": "timer{f:08d}".format(f=i), "class": "es", "text-anchor": "middle"})
    t.string="Time{}".format(i)
    st = soup.new_tag("text", attrs={"class": "er", "style": "fill: #000000", "text-anchor": "middle", "x": 128, "y": i * 100 + 27})
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
    u = soup.new_tag("use", attrs={"height": 30, "id": "sys{f:08d}".format(f=i), "width": 62.5, "x": 100, "xlink:href": "#def{f:08d}".format(f=i), "y": i*100+16})
    use[0].append(u)
    onload += "var field{n:1} = document.querySelector('#timer{t:08d}');\nvar delay{n:1} = {n:1} * 60;\nstartTimer(delay{n:1}, field{n:1});\n".format(t=i, n=i)
# defs = body.find("defs")
# if not defs:
#     print("no spot to put")
#     exit(1)
# defs.append(output)

startjs = "window.onload = function () {\n"+onload+"\n}"
js = soup.new_tag("script", attrs={"type": "text/javascript"})
js.string = CData(realtime_js)

# header.append(js)
js = soup.new_tag("script", attrs={"type": "text/javascript"})
js.string = startjs
# header.append(js)
with open("providencecatch1.svg", "w") as f:
    f.write(soup.prettify())

