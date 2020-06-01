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
from vi.states import State
from colour import Color
from vi.settings.settings import ColorSettings


class ColorJavaScript:
    WHITE = "#ffffff"
    BLACK = "#000000"
    DEFAULT = [
        [60 * 2, "#59FF6C", "#000000"],
    ]

    def __init__(self):
        self.cache = Cache()
        self.js_header = [
            "Starting Color for... (seconds)",
            "Background Color",
            "Text Color",
        ]
        self.js_lst = ColorSettings().js_alarm_colors
        self.color_arrays = {}

    @staticmethod
    def show_timer() -> str:
        realtime_js = """
        var UNKNOWN_COLOR = "#FFFFFF";
        var CLEAR_COLOR = "#59FF6C";
        var STATE = ['alarm', 'was alarmed', 'clear', 'unknown', 'ignore', 'no change', 'request', 'location'];
        // seconds since a state has been announced, state, text-line to place text, Rectangle, Ice-Rectangle
        function showTimer(current_time, state, second_line, rect, rect_ice) {
            var color_list;
            var text_background = '#000000';
            // analysing list
            var analyse;
            if (state == STATE[0]) { // Alarm
                analyse = ALARM_COLORS;
            }
            else if (state == STATE[2]) { // Clear
                analyse = CLEAR_COLORS;
            }
            else if (state == STATE[6]) { // Request
                analyse = REQUEST_COLORS;
            }
            var array_offset = 0;
            var array_length = 0;
            // until when this color is active
            var max_time = 0;
            // inital Time-Stamp when the Interval is being activated
            var start_time = new Date().getTime() - (current_time * 1000);
            window.setInterval(function() {
                var time = new Date().getTime() - start_time;
                // time spent in this timer
                var elapsed = (Math.ceil(time / 100) / 10).toFixed();
                if (elapsed < 0) {
                    return;
                }
                if ((elapsed >= max_time) && (array_offset < analyse.length / 6)) {
                    while ((array_offset < analyse.length / 6) && (elapsed > max_time)) {
                        text_background = analyse[array_offset * 6 + 4].toString();
                        max_time = analyse[array_offset * 6];
                        color_list = analyse[array_offset * 6 + 5];
                        array_length = analyse[array_offset * 6 + 1];
                        array_offset += 1;
                    }
                }
                var index = elapsed >= max_time ? array_length-1 : (elapsed % array_length);
                var minutes = parseInt(elapsed / 60, 10);
                var seconds = parseInt(elapsed % 60, 10);
                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;
                second_line.setAttribute("style", "fill: " + text_background);
                var new_color = color_list[index].toString();
                rect.setAttribute("style", "fill: " + new_color);
                rect_ice.setAttribute("style", "fill: " + new_color);
                second_line.textContent = minutes + ":" + seconds;
            }, 1000);
        }
        """
        return realtime_js

    def all_colors_in_string(self) -> str:
        return self.js_color_all()

    def get_keys(self):
        state_list = []
        for key in self.js_lst.keys():
            state_list.append(key.name.upper())

        return state_list

    def js_color_all(self):
        return_str = ""
        for color in self.js_lst.keys():
            return_str += self.js_color_string(color)
        return return_str

    def color_array(self, status: State) -> list:
        """return an array with Color and Timing for the duration of the State.
        If the State doesn't exist, return a default
        """
        if status not in self.color_arrays.keys():
            color_array = []
            color_range = self.status_list(status)
            time_offset = 0
            for index, color_index in enumerate(self.js_lst[status]):
                start_color = Color(color_index[1])
                if index == len(color_range) - 1:  # last reached
                    end_color = self.WHITE
                else:
                    end_color = color_range[index + 1][1]
                length = color_index[0] - time_offset
                set_color = list(start_color.range_to(end_color, length))
                color_array.append(
                    [
                        color_index[0],
                        length,
                        color_index[1],
                        end_color,
                        color_index[2],
                        [c.get_hex_l() for c in set_color],
                    ]
                )
                time_offset = color_index[0]
            self.color_arrays[status] = color_array
        return self.color_arrays[status]

    def js_color_string(self, status: State):
        """create a JS-Line with a Color-Definition.

        The JS-Array is of the following format:
        up-to-duration, duration, start-color, end-color, text-color, [ <duration> list of colors ]
        """
        color_array = self.color_array(status)
        output = "var %s_COLORS = [" % (status.name.upper(),)
        for color_range in color_array:
            s_color = "\n   %d, %d, '%s', '%s', '%s' , %s," % (
                color_range[0],
                color_range[1],
                color_range[2],
                color_range[3],
                color_range[4],
                str([c for c in color_range[5]]),
            )
            output += s_color
        output = output.rstrip(",") + "\n];\n"
        return output

    def status_list(self, status: State) -> list:
        if status not in self.js_lst.keys():
            self.js_lst[status] = self.DEFAULT
        return self.js_lst[status]

    def max_time(self, status: State) -> int:
        check_arr = self.color_array(status)
        if check_arr:
            return check_arr[-1][0]
        return 60 * 60 * 24

    def color_at(self, time_in_secs: int, status: State) -> tuple:
        # get the colors
        check_array = self.color_array(status)
        if not check_array or time_in_secs >= check_array[-1][0]:
            return self.WHITE, self.BLACK
        for section in check_array:
            if time_in_secs >= section[0]:
                continue
            offset = time_in_secs - (section[0] - section[1])
            return section[5][offset], section[4]
        return self.WHITE, self.BLACK

    def get_last(self, status: State) -> tuple:
        return self.color_at(60 * 60 * 24, status)

    def save_settings(self):
        ColorSettings().js_alarm_colors = self.js_lst


if __name__ == "__main__":
    cjs = ColorJavaScript()
    # print(cjs.get_last('alarm'))
    al = cjs.color_array(State["IGNORE"])
    print(al)
    print(al[-1][0] + al[-1][1])
    print(cjs.js_lst.keys())
    print("Max-Time alarm: %d" % cjs.max_time("alarm"))
    print("Max-Time clear: %d" % cjs.max_time("clear"))
    print("Max-Time request: %d" % cjs.max_time("request"))
    print("Max-Time bla: %d" % cjs.max_time("bla"))
    print(cjs.color_array())
    for sec in cjs.color_array():
        print(sec)
    print("Color at 0: %r" % (cjs.color_at(0),))
    print("Color at 1: %r" % (cjs.color_at(1),))
    print("Color at 601: %s" % (cjs.color_at(601),))
    # print(cjs.js_color_string('alarm'))

    # qq = cjs.create_js_color("alarm")
    # print(qq)
