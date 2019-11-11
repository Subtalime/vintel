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

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
from vi.cache.cache import Cache
from vi.dotlan.regions import Regions
from vi.resources import resourcePath, getVintelMap
import logging
from vi.ui.RegionChooserList import Ui_Dialog

LOGGER = logging.getLogger(__name__)


class RegionChooserList(QtWidgets.QDialog, Ui_Dialog):
    new_region_range_chosen = pyqtSignal(str)

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cancelButton.clicked.connect(self.reject)
        self.saveButton.clicked.connect(self.saveClicked)
        self.helpButton.clicked.connect(self.helpClicked)
        self.regionNames = []
        cacheRegions = Cache().getFromCache("region_name_range")
        if cacheRegions:
            self.regionNames = cacheRegions.split(",")
            for name in self.regionNames:
                if name is None or name == "":
                    self.regionNames.pop()

        self.allRegions = Regions()
        for region in self.allRegions.getNames():
            item = QtWidgets.QListWidgetItem(region)
            self.listWidget.addItem(item)
        for region in self.regionNames:
            items = self.listWidget.findItems(region, QtCore.Qt.MatchExactly)
            if items:
                items[0].setSelected(True)
            else:
                if len(self.txtRegions.text()) > 0:
                    self.txtRegions.setText(self.txtRegions.text() + ",")
                self.txtRegions.setText(self.txtRegions.text() + region)

    def checkMapFiles(self) -> bool:
        if self.txtRegions.text():
            self.txtRegions.setText(self.txtRegions.text().replace(" ", ""))
            regions = self.txtRegions.text().split(",")
            for region in regions:
                if not region.endswith(".svg"):
                    return False
                from os.path import isfile
                if not isfile(getVintelMap(region)):
                    return False
        return True

    def saveClicked(self):
        if not self.checkMapFiles():
            resPath = getVintelMap()
            QMessageBox.critical(None, "Region selection",
                                 "Regions must end with \".svg\" and exist in \"{}\"\n{}".format(
                                     resPath,
                                     self.txtRegions.text()))
            self.txtRegions.setFocus()
            return

        items = self.listWidget.selectedItems()
        litems = []
        for item in items:
            if len(item.text()) > 0:
                litems.append(item.text())
        saveCache = ",".join(litems)
        if len(litems) > 0 and self.txtRegions.text():
            saveCache += "," + self.txtRegions.text()
        Cache().putIntoCache("region_name_range", saveCache, 60 * 60 * 24 * 365)
        LOGGER.info("New list of Regions selected: {}".format(saveCache))
        self.new_region_range_chosen.emit(saveCache)
        self.accept()

    def helpClicked(self):
        # open a Help-Dialog
        try:
            with open(resourcePath("docs/regionselect.txt")) as f:
                content = f.read()
                content = content.replace("<mapdir>", getVintelMap())
                QMessageBox.information(None, "Region-Help", content)
        except FileNotFoundError:
            QMessageBox.warning(None, "Help-File",
                                "Unable to find Help-File \n{}".format(
                                    resourcePath("docs/regionselect.txt")))
