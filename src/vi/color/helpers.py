#  Vintel - Visual Intel Chat Analyzer
#  Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog


def string_to_color(string_color: str = None) -> QColor:
    if str(string_color).startswith("#"):
        color = str(string_color).lstrip("#")
        lv = len(color)
        cs = tuple(int(color[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))
    else:
        cs = [0, 0, 0]
    return QColor(cs[0], cs[1], cs[2])


def color_dialog(color=QColor()):
    return QColorDialog().getColor(initial=color)


def contrast_color(one_color: QColor) -> str:
    # Calculate the perceptive luminance (aka luma) - human eye favors green color...
    luma = (
        (0.299 * one_color.red())
        + (0.587 * one_color.green())
        + (0.114 * one_color.blue())
    ) / 255
    # Return black for bright colors, white for dark colors
    return "#000000" if luma > 0.5 else "#ffffff"


if __name__ == "__main__":
    test = string_to_color("#ff3355")
    res = contrast_color(test)
    print(test.value(), res)
