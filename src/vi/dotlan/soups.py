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

from bs4.element import ResultSet, Tag


class SoupRect:
    def __init__(self, soup_rect: Tag):
        self._rect = soup_rect

    @property
    def id(self) -> str:
        return self._rect["xlink:href"][1:]
        # return self._rect["id"] or None

    @property
    def style(self) -> str:
        return self._rect["style"] or None

    @style.setter
    def style(self, value: str):
        self._rect["style"] = value

    @property
    def x(self) -> float:
        return float(self._rect["x"])

    @x.setter
    def x(self, value: float):
        self._rect["x"] = float(value)

    @property
    def rx(self) -> float:
        return float(self._rect["rx"])

    @rx.setter
    def rx(self, value: float):
        self._rect["rx"] = float(value)

    @property
    def y(self) -> float:
        return float(self._rect["y"])

    @y.setter
    def y(self, value: float):
        self._rect["y"] = float(value)

    @property
    def ry(self) -> float:
        return float(self._rect["ry"])

    @ry.setter
    def ry(self, value: float):
        self._rect["ry"] = float(value)

    @property
    def w(self) -> float:
        return float(self._rect["width"])

    @w.setter
    def w(self, value: float):
        self._rect["width"] = float(value)

    @property
    def width(self) -> float:
        return self.w

    @width.setter
    def width(self, value: float):
        self.w = value

    @property
    def h(self) -> float:
        return float(self._rect["height"])

    @h.setter
    def h(self, value: float):
        self._rect["height"] = float(value)

    @property
    def height(self) -> float:
        return self.h

    @height.setter
    def height(self, value: float):
        self.h = value

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def as_dict(self) -> dict:
        map_coordinates = {}
        map_coordinates["x"] = self.x
        map_coordinates["y"] = self.y
        map_coordinates["width"] = self.w
        map_coordinates["height"] = self.h

        # for key_name in ("x", "y", "width", "height"):
        #     map_coordinates[key_name] = eval(self.key_name)
        map_coordinates["center_x"] = self.cx
        map_coordinates["center_y"] = self.cy
        return map_coordinates

    def __repr__(self):
        return f"x:{self.x} y:{self.y} w:{self.w} h:{self.h}"


class SoupUse:
    def __init__(self, result_set: Tag):
        self.use = result_set

    @property
    def id(self) -> str:
        return self.use["xlink:href"][1:]

    @property
    def n_coordinates(self) -> dict:
        map_coordinates = {}
        for key_name in ("x", "y", "width", "height"):
            map_coordinates[key_name] = float(self.use[key_name])
        map_coordinates["center_x"] = map_coordinates["x"] + (
                map_coordinates["width"] / 2
        )
        map_coordinates["center_y"] = map_coordinates["y"] + (
                map_coordinates["height"] / 2
        )
        return map_coordinates

    @property
    def coordinates(self) -> SoupRect:
        return SoupRect(self.use)



    @property
    def transform(self) -> list:
        return [0.0, 0.0]
        # try:
        #     transform = self.use["transform"]
        # except KeyError:
        #     transform = "translate(0,0)"
        # return transform


class SoupSystem:
    def __init__(self, result_set: Tag, result_coords: SoupRect = None):
        self._system = result_set
        self._coordinates = result_coords

    @property
    def valid(self) -> bool:
        return len(self.name) > 0

    @property
    def symbol_id(self) -> str:
        return self._system["id"]

    @property
    def system(self) -> Tag:
        return self._system

    @property
    def system_id(self) -> int:
        return int(self.symbol_id[3:])

    @property
    def sys_elements(self) -> ResultSet:
        return self._system.select(".sys")

    @property
    def sys_element(self) -> Tag:
        return self.sys_elements[0]

    # @property
    # def rects(self) -> list:
    #     rl = []
    #     for r in self._system.findAll("rect"):
    #         rl.append(SoupRect(r))
    #     return rl

    @property
    def rect(self) -> SoupRect:
        return self._coordinates

    @property
    def texts(self) -> ResultSet:
        return self._system.findAll("text")

    @property
    def name(self) -> str:
        try:
            return self.sys_elements[0].select("text")[0].text.strip().upper()
        except IndexError:
            return ""

    @property
    def label(self) -> str:
        return self.name.replace("-", "_").lower()

    @property
    def coordinates(self) -> SoupRect:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, value: SoupRect):
        self._coordinates = value

    @property
    def transform(self) -> list:
        return [0., 0.]

    @property
    def rectangles(self) -> ResultSet:
        return self._system.select("rect")

    @property
    def lines(self) -> ResultSet:
        return self.texts

    @property
    def line_one(self) -> Tag:
        return self.lines[0]

    @line_one.setter
    def line_one(self, value: Tag):
        self.lines[0] = value

    @property
    def line_two(self) -> Tag:
        return self.lines[1]

    @line_two.setter
    def line_two(self, value: Tag):
        self.lines[1] = value

