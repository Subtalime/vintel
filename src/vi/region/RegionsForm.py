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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from os.path import isfile
import os
from vi.settings.SettingsFormTemplate import SettingsFormTemplate
from vi.settings.settings import RegionSettings
from vi.ui.RegionsForm import Ui_Form
from vi.dotlan.regions import Regions
from vi.resources import resourcePath, getVintelMap


class RegionsForm(SettingsFormTemplate, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btnRegionHelp.clicked.connect(self.region_help_clicked)

        region_names = []
        # self.cache_regions = Cache().fetch("region_name_range")
        self.cache_regions = RegionSettings().region_names
        if self.cache_regions:
            region_names = self.cache_regions.split(",")
            for name in region_names:
                if name is None or name == "":
                    region_names.pop()

        for region in Regions().getNames():
            item = QListWidgetItem(region)
            self.listRegion.addItem(item)
        for region in region_names:
            items = self.listRegion.findItems(region, Qt.MatchExactly)
            if items:
                items[0].setSelected(True)
            else:
                if len(self.txtRegions.text()) > 0:
                    self.txtRegions.setText(self.txtRegions.text() + ",")
                self.txtRegions.setText(self.txtRegions.text() + region)
        self.txtRegions.editingFinished.connect(self.region_check_mapfile)
        self.listRegion.clicked.connect(self.change_detected)

    def region_check_mapfile(self) -> bool:
        success = True
        if self.txtRegions.text():
            self.txtRegions.setText(self.txtRegions.text().replace(" ", ""))
            regions = self.txtRegions.text().split(",")
            for region in regions:
                if not region.endswith(".svg"):
                    success = False
                if not isfile(getVintelMap(region)):
                    success = False
            if not success:
                files = []
                for file in os.listdir(getVintelMap()):
                    if file.endswith(".svg"):
                        files.append(file)
                        QMessageBox.critical(
                            self,
                            "Region selection",
                            'Regions must end with ".svg" '
                            'and exist in "{dirpath}\nExisting files '
                            'are:{files}"'.format(dirpath=getVintelMap(), files=files),
                        )
                self.txtRegions.setFocus()
        if success:
            self.change_detected()
        return success

    def region_help_clicked(self):
        # open a Help-Dialog
        try:
            with open(resourcePath("docs/regionselect.txt")) as f:
                content = f.read()
                content = content.replace("<mapdir>", getVintelMap())
                QMessageBox.information(None, "Region-Help", content)
        except FileNotFoundError:
            QMessageBox.warning(
                None,
                "Help-File",
                "Unable to find Help-File \n{}".format(
                    resourcePath("docs/regionselect.txt")
                ),
            )

    def _get_selected(self):
        litems = []
        for item in self.listRegion.selectedItems():
            if len(item.text()) > 0:
                litems.append(item.text())
        region_list = ",".join(litems)
        if self.txtRegions.text():
            region_list += "," + self.txtRegions.text()
        return region_list.lstrip(",")

    def save_data(self):
        RegionSettings().region_names = self._get_selected()

    @property
    def data_changed(self) -> bool:
        return self._get_selected() != RegionSettings().region_names


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = RegionsForm()
    d.show()
    sys.exit(a.exec_())
