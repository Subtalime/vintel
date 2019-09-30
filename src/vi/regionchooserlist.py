from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from vi.cache.cache import Cache
from vi import dotlan
import logging

from vi.ui.RegionChooserList import Ui_Dialog
class RegionChooserList(QtWidgets.QDialog, Ui_Dialog):
    new_region_range_chosen = pyqtSignal()

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cancelButton.clicked.connect(self.accept)
        self.saveButton.clicked.connect(self.saveClicked)
        cacheRegions = Cache().getFromCache("region_name_range")
        if cacheRegions:
            self.regionNames = cacheRegions.split(",")
        self.allRegions = dotlan.Regions()
        for region in self.allRegions.getNames():
            item = QtWidgets.QListWidgetItem(region)
            if region in self.regionNames:
                item.setSelected(True)
            self.listWidget.addItem(item)

    def saveClicked(self):
        items = self.listWidget.selectedItems()
        saveCache = ",".join(items)
        Cache().putIntoCache("region_name_range", saveCache, 60 * 60 * 24 * 365)
        logging.info("New list of Regions selected: {}".format(saveCache))
        self.accept()
        self.new_region_range_chosen.emit()

