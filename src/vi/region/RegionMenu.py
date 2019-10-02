from PyQt5.QtWidgets import QMenu, QListWidget, QAction, QAbstractItemView, QActionGroup
from vi.cache.cache import Cache
import logging

class RegionMenu(QMenu):
    def __init__(self, menuname: 'str', parent: 'QObject' = None):
        super(RegionMenu, self).__init__(menuname, parent)
        self.group = QActionGroup(self, exclusive=True)
        self._menu_actions = dict()
        self.selectedRegion = None
        self.regionNames = ["Delve"]
        self.addItems()

    def _actionName(self, region: 'str'):
        return str(region).replace(' ', '_').replace('-', '_') + "_action"

    def addItem(self, region: 'str'):
        if region in self._menu_actions.keys():
            return None
        action = QAction(region, self, checkable=True)
        action.setData(self._actionName(region))
        action.setProperty("regionName", region)
        action.setObjectName(region)
        action.setChecked(region == self.selectedRegion)
        # action.triggered.connect(self.region_selected)
        self._menu_actions[region] = action
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
        logging.debug("Updating Region-Menu with {}".format(regionNames))
        if regionNames:
            self.regionNames = regionNames.split(",")
        self.regionNames.sort()
        self.selectedRegion = Cache().getFromCache("region_name", True)
        if not self.selectedRegion in self.regionNames:
            self.selectedRegion = self.regionNames[0]
            Cache().putIntoCache("region_name", self.selectedRegion)
        for region in self.regionNames:
            self.addItem(region)
        self._addRemainder()

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
        except Exception as e:
            raise
