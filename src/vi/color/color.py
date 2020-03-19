#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
from colour import Color
from dataclasses import dataclass

@dataclass
class ColorGradient:
    text: str
    start: str
    end: str
    duration: int

    @classmethod
    def set(cls, duration: int, start: str, end: str, text: str):
        return ColorGradient(duration=duration, start=start, end=end, text=text)


class ColorStatus(object):
    def __init__(self, type: str = "Alarm"):
        self.type = type
        self.ranges = []

    def add(self, duration, background, text):
        for ending in self.ranges:
            if ending.duration < duration
        g = ColorGradient.set(duration, start, end)
        self.ranges.append(g)
        self.ranges.sort(key=lambda l: l.duration)

    def get_interval(self, time: int):
        t = 0
        for grad in self.ranges:
            t += grad.duration
            if time <= t:
                return list(Color(cls.start).range_to(cls.end, cls.duration + 1))[interval].get_hex_l()
                return "#ffffff"  # WHITE
                return grad.get_interval(t - time)


if __name__ == "__main__":
    cs = ColorStatus()
    cs.add(10, 1, 10)
    cs.add(40, 11, 40)
    v = cs.get_interval(40)
    print(v)

