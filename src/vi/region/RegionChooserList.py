from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QErrorMessage, QMessageBox
from PyQt5.QtCore import pyqtSignal
from vi.cache.cache import Cache
from vi.dotlan.regions import Regions
from vi.resources import resourcePath
import logging
from vi.ui.RegionChooserList import Ui_Dialog


class RegionChooserList(QtWidgets.QDialog, Ui_Dialog):
    new_region_range_chosen = pyqtSignal(str)

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cancelButton.clicked.connect(self.accept)
        self.saveButton.clicked.connect(self.saveClicked)
        self.regionNames = []
        cacheRegions = Cache().getFromCache("region_name_range")
        if cacheRegions:
            self.regionNames = cacheRegions.split(",")
        self.allRegions = Regions()
        for region in self.allRegions.getNames():
            item = QtWidgets.QListWidgetItem(region)
            self.listWidget.addItem(item)
        for region in self.regionNames:
            for item in self.listWidget.findItems(region, QtCore.Qt.MatchExactly):
                item.setSelected(True)
                break
            if not item:
                if len(self.txtRegions.text()) > 0:
                    self.txtRegions.setText(self.txtRegions.text()+",")
                self.txtRegions.setText(self.txtRegions.text()+region)

    def checkMapFiles(self) -> bool:
        if self.txtRegions.text():
            regions = self.txtRegions.text().split(",")
            for region in regions:
                if not region.endswith(".svg"):
                    return False
                from os.path import isfile
                if not isfile(resourcePath("vi/ui/res/mapdata/"+region)):
                    return False
        return True

    def saveClicked(self):
        if not self.checkMapFiles():
            resPath = resourcePath("vi/ui/res/mapdata/")
            err = QMessageBox()
            err.move(self.rect().center())
            err.critical(None, "Regions must end with \".svg\" and exist in \"{}\"".format(resPath), self.txtRegions.text())
            err.exec_()
            self.txtRegions.setFocus()
            return

        items = self.listWidget.selectedItems()
        litems = []
        for item in items:
            litems.append(item.text())
        saveCache = ",".join(litems)
        if len(litems) > 0:
            saveCache += ","+self.txtRegions.text()
        Cache().putIntoCache("region_name_range", saveCache, 60 * 60 * 24 * 365)
        logging.info("New list of Regions selected: {}".format(saveCache))
        self.accept()
        self.new_region_range_chosen.emit(saveCache)

