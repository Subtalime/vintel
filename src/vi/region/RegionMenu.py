from PyQt5.QtWidgets import QMenu, QListWidget, QListWidgetItem, QAction, QAbstractItemView
from vi.dotlan import Regions
from vi.cache.cache import Cache
from collections import OrderedDict

class RegionMenu(QMenu):
    def __init__(self, menuname: 'str', parent: 'QObject' = None):
        super(RegionMenu, self).__init__(menuname, parent)
        self._listWidget = QListWidget()
        self._listWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self._menu_actions = dict()
        self._availableRegions = Regions()
        regionName = Cache().getFromCache("region_name")
        if not regionName:
            regionName = u"Delve"
        self.regionNames = [regionName]
        self.selectedRegion = regionName

    def _actionName(self, region):
        return str(region).replace(' ', '_').replace('-', '_') + "_action"

    def addItem(self, region: 'str'):
        if region in self._menu_actions.keys():
            return False
        action = QAction(region, self, checkable=True)
        action.setData(self._actionName(region))
        action.setObjectName(region)
        action.setChecked(region == self.selectedRegion)
        self._menu_actions[region] = action
        self.addAction(action)
        return True

    def _addRemainder(self):
        self.addSeparator()
        action = QAction("Region select...", self)
        action.setData("region_select_action")
        self._menu_actions["select"] = action
        self.addAction(action)
        self.addSeparator()
        action = QAction("Jumpbridge data...", self)
        action.setData("jumpbridge_select_action")
        self._menu_actions["jumpbridge"] = action
        self.addAction(action)

    def addItems(self):
        self.removeItems()
        cache = Cache()
        regionNames = cache.getFromCache("region_name_range")
        if regionNames:
            self.regionNames = regionNames.split(",")
        od = OrderedDict(sorted(self.regionNames))
        for region in od:
            self.addItem(region)
        self._addRemainder()

    def removeItems(self):
        try:
            for menuitem in self._menu_actions:
                obj = self.findChild(QAction, menuitem)
                if obj:
                    self.removeAction(obj)
            self._menu_actions = dict()
        except Exception as e:
            raise

