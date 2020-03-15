#    Vintel - Visual Intel Chat Analyzer
#    Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
from vi.cache.cache import Cache
from vi.singleton import Singleton
import pickle
import six
import logging
from colorutils import Color, color_run


class ColorJavaScript(six.with_metaclass(Singleton)):
    def __init__(self):
        self.cache = Cache()
        self.js_header = ["Starting Color for... (seconds)", "Background Color", "Text Color"]
        self.js_lst = None
        self.load_settings()
        self.LOGGER = logging.getLogger(__name__)

    def getJs(self):
        return_str = ""
        for p, val in self.js_lst.items():
            return_str += "var {}_COLORS = [".format(str(p).upper())
            for a, b, c in val:
                return_str += " {}, '{}', '{}',".format(a, b, c)
            return_str = return_str.rstrip(",")
            return_str += " ];\n        "
        return return_str

    def get_color(self, time_in_secs, status: str) -> tuple:
        lenc = len(self.js_lst[status.capitalize()])
        nextc = 0
        timerange = 0
        startc = Color()
        endc = Color()
        for lst in self.js_lst[status.capitalize()]:
            timerange += lst[0]
            nextc += 1
            if time_in_secs < timerange:
                startc.hex = lst[1]
                if nextc == lenc:
                    endc.hex = '#ffffff'
                else:
                    endc.hex = self.js_lst[status.capitalize()][nextc][1]
                try:
                    ccolor = color_run(startc, endc, lst[0] - 1)[time_in_secs - timerange]
                except IndexError:
                    self.LOGGER.error(
                        "Index-Error: %r, %d-%d=%d" % (lst, time_in_secs, timerange, time_in_secs - timerange))
                    ccolor = color_run(startc, endc, lst[0])[time_in_secs - timerange]

                return ccolor.hex, lst[2]
        return '#ffffff', '#000000'

    def load_settings(self):
        content = self.cache.getFromCache("js_alarms")
        if content:
            self.js_lst = pickle.loads(content)
        else:
            self.js_lst = {"Alarm": [[60 * 4, "#FF0000", "#FFFFFF"], [60 * 10, "#FF9B0F", "#000000"],
                                     [60 * 15, "#FFFA0F", "#000000"], [60 * 25, "#FFFDA2", "#000000"],
                                     [60 * 60 * 24, "#FFFFFF", "#000000"]],
                           "Request": [[60 * 2, "#ffaaff", "#000000"],
                                       [60 * 60 * 24, "#FFFFFF", "#000000"]],
                           "Clear": [[60 * 2, "#59FF6C", "#000000"],
                                     [60 * 60 * 24, "#FFFFFF", "#000000"]]
                           }

    def save_settings(self):
        self.cache.putIntoCache("js_alarms", pickle.dumps(self.js_lst))
