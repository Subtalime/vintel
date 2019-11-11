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

from PyQt5.QtWidgets import QMenu, QAction, QActionGroup
from PyQt5.QtCore import QObject
from vi.cache.cache import Cache
import logging

LOGGER = logging.getLogger(__name__)


def getRegionName(word: str):
    if word.endswith(".svg"):
        regionName = word.replace(".svg", "")
    else:
        regionName = word
    return regionName


class RegionMenu(QMenu):
    def __init__(self, menuname: str, parent: QObject = None):
        super(RegionMenu, self).__init__(menuname, parent)
        self.group = QActionGroup(self, exclusive=True)
        self._menu_actions = dict()
        self.selectedRegion = None
        self.regionNames = ["Delve"]
        self.addItems()

    @staticmethod
    def _actionName(region: str) -> str:
        return str(region).replace(' ', '_').replace('-', '_') + "_action"

    def addItem(self, regionName: str) -> QAction:
        if regionName in self._menu_actions.keys():
            return None
        action = QAction(regionName, self, checkable=True)
        action.setData(self._actionName(regionName))
        action.setProperty("regionName", regionName)
        action.setObjectName(regionName)
        action.setChecked(regionName == self.selectedRegion)
        self._menu_actions[regionName] = action
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

    def addItems(self):
        self.removeItems()
        regionNames = Cache().getFromCache("region_name_range")
        LOGGER.debug("Updating Region-Menu with {}".format(regionNames))
        if regionNames:
            self.regionNames = [getRegionName(y) for y in regionNames.split(",")]
            for name in self.regionNames:
                if name is None or name == "":
                    self.regionNames.pop()
        self.regionNames.sort()
        self.selectedRegion = self.getSelectedRegion
        if self.selectedRegion not in self.regionNames:
            self.selectedRegion = self.regionNames[0]
            Cache().putIntoCache("region_name", self.selectedRegion)
        for region in self.regionNames:
            self.addItem(region)
        self._addRemainder()

    @property
    def getSelectedRegion(self) -> str:
        return Cache().getFromCache("region_name", True)

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
