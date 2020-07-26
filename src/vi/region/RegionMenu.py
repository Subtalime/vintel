#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
#

import logging

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QAction, QActionGroup, QMenu

from vi.cache.cache import Cache
from vi.settings.settings import RegionSettings

LOGGER = logging.getLogger(__name__)


def get_region_name(word: str):
    if word.endswith(".svg"):
        region_name = word.replace(".svg", "")
    else:
        region_name = word
    return region_name.capitalize()


class RegionMenu(QMenu):
    def __init__(self, menuname: str, parent: QObject = None):
        super(RegionMenu, self).__init__(menuname, parent)
        self.group = QActionGroup(self)
        self.group.setExclusive(True)
        self._menu_actions = dict()
        self.regionNames = ["Delve"]
        self.addItems()

    @staticmethod
    def _action_name(region: str) -> str:
        return str(region).replace(" ", "_").replace("-", "_") + "_action"

    def addItem(self, region_name: str) -> QAction:
        if region_name in self._menu_actions.keys():
            return QAction()
        action = QAction(region_name, self)
        action.setCheckable(True)
        action.setData(self._action_name(region_name))
        action.setProperty("region_name", region_name)
        action.setObjectName(region_name)
        action.setChecked(region_name == self.selectedRegion)
        self._menu_actions[region_name] = action
        a = self.group.addAction(action)
        self.addAction(a)
        return a

    def _addRemainder(self):
        self.addSeparator()
        action = QAction("Region select...", self)
        action.setData("region_select_action")
        action.setObjectName("region_select")
        self._menu_actions["select"] = action
        self.addAction(action)
        self.addSeparator()
        action = QAction("Jumpbridge data...", self)
        action.setData("jumpbridge_select_action")
        action.setObjectName("jumpbridge_select")
        self._menu_actions["jumpbridge"] = action
        self.addAction(action)

    def addItems(self, region_names: str = None):
        """removes all Region-Menu items and re-creates

        :param region_names: string of region names separated by commas. None = loads settings
        :type region_names: str
        :return:
        """
        self.removeItems()
        # regionNames = Cache().fetch("region_name_range")
        if not region_names:
            region_names = RegionSettings().region_names
        LOGGER.debug("Updating Region-Menu with %s", region_names)
        if region_names:
            self.regionNames = [get_region_name(y) for y in region_names.split(",")]
            for name in self.regionNames:
                if name is None or name == "":
                    self.regionNames.pop()
        self.regionNames.sort()
        if self.selectedRegion not in self.regionNames:
            self.selectedRegion = self.regionNames[0]
        for region in self.regionNames:
            self.addItem(region)
        self._addRemainder()

    @property
    def selectedRegion(self) -> str:
        return RegionSettings().selected_region
        # return Cache().fetch("region_name", True)

    @selectedRegion.setter
    def selectedRegion(self, value):
        RegionSettings().selected_region = value
        # Cache().put("region_name", value)

    def removeItems(self):
        try:
            for action in self.group.actions():
                self.group.removeAction(action)
            for action in self.actions():
                if not isinstance(action, QActionGroup):
                    self.removeAction(action)
            for menuitem in self._menu_actions:
                action = self.findChild(QAction, menuitem)
                if action:
                    self.removeAction(action)
            self._menu_actions = dict()
        except Exception:
            raise


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    men = RegionMenu("Regions")

    app.exec_()
