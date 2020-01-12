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

import os
from ast import literal_eval
from os.path import isfile
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import pyqtSignal, QModelIndex, Qt, QAbstractTableModel, QVariant
from vi.settings.JsModel import stringToColor, dialogColor, JsModel
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.ui.Settings import Ui_Dialog
from vi.cache.cache import Cache
from vi.dotlan.regions import Regions
from vi.resources import soundPath, resourcePath, getVintelMap
from vi.sound.soundmanager import SoundManager


class SettingsDialog(QDialog, Ui_Dialog):
    settings_saved = pyqtSignal()
    new_region_range_chosen = pyqtSignal(str)
    rooms_changed = pyqtSignal(list)

    class SoundTableModel(QAbstractTableModel):
        layout_to_be_changed = pyqtSignal()
        layout_changed = pyqtSignal()

        def __init__(self, datain, headerdata, parent=None):
            """
            Args:
                datain: a list of lists\n
                headerdata: a list of strings
            """
            QAbstractTableModel.__init__(self, parent)
            self.arraydata = datain
            self.headerdata = headerdata

        def rowCount(self, parent=None):
            return len(self.arraydata)

        def columnCount(self, parent=None):
            if len(self.arraydata) > 0:
                return len(self.arraydata[0])
            return 0

        def data(self, index, role=Qt.DisplayRole):
            if not index.isValid():
                return QVariant()
            elif role != Qt.DisplayRole:
                return QVariant()
            return QVariant(self.arraydata[index.row()][index.column()])

        def setData(self, index, value, role=Qt.EditRole):
            if not index.isValid():
                return False
            if role != Qt.EditRole:
                return False
            self.arraydata[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True

        def getDataSet(self):
            return self.arraydata

        def getData(self, index):
            if not index.isValid():
                return None
            return self.arraydata[index.row()][index.column()]

        def getDataRow(self, row):
            return self.arraydata[row]

        def headerData(self, col, orientation, role):
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return QVariant(self.headerdata[col])
            return QVariant()

        def sort(self, Ncol, order):
            """
            Sort table by given column number.
            """
            self.layout_to_be_changed.emit()
            self.arraydata = sorted(self.arraydata, key=lambda operator: operator[Ncol])
            if order == Qt.DescendingOrder:
                self.arraydata.reverse()
            self.layout_changed.emit()

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.color = None
        self.setWindowTitle("Vintel Settings")
        # Everything to do with Map-Colors
        self.java_script = ColorJavaScript()
        self.mapColorList = self.java_script.js_lst.copy()
        self.mapColorIndex = 0
        self.model = JsModel(self.mapColorList['Alarm'], self.java_script.js_header)
        self.tableViewMap.setModel(self.model)
        self.tableViewMap.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableViewMap.resizeColumnsToContents()
        self.tableViewMap.setSortingEnabled(True)
        self.tableViewMap.sortByColumn(0, Qt.AscendingOrder)
        self.tableViewMap.doubleClicked.connect(self.map_select_color)
        self.tableViewMap.clicked.connect(self.map_select_color)
        self.cmbAlertType.addItems(self.mapColorList.keys())
        self.cmbAlertType.currentIndexChanged.connect(self.set_map_table_model)
        self.btnMapAddTime.clicked.connect(self.map_add_color_row)
        self.btnMapDelTime.clicked.connect(self.map_remove_color_row)
        # all General settings
        self.btnColor.clicked.connect(self.color_chooser)
        self.buttonBox.accepted.connect(self.save_settings)
        self.buttonBox.rejected.connect(self.cancel_setting)
        self.txtKosInterval.setEnabled(False)
        # all Sound Settings
        self.sound_setup()
        # all Region Settings
        self.region_setup()
        # Chatroom Settings
        self.chatroom_setup()

    def chatroom_setup(self):
        roomnames = Cache().getFromCache("room_names")
        if not roomnames:
            roomnames = u"querius.imperium,delve.imperium"
        self.txtChatrooms.setPlainText(roomnames)

    def region_setup(self):
        self.btnRegionHelp.clicked.connect(self.region_help_clicked)

        region_names = []
        cache_regions = Cache().getFromCache("region_name_range")
        if cache_regions:
            region_names = cache_regions.split(",")
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

    def region_check_mapfile(self) -> bool:
        if self.txtRegions.text():
            self.txtRegions.setText(self.txtRegions.text().replace(" ", ""))
            regions = self.txtRegions.text().split(",")
            for region in regions:
                if not region.endswith(".svg"):
                    return False
                if not isfile(getVintelMap(region)):
                    return False
        return True

    def region_help_clicked(self):
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

    def region_save(self) -> bool:
        if not self.region_check_mapfile():
            QMessageBox.critical(None, "Region selection",
                                 "Regions must end with \".svg\" and exist in \"{}\"\n{}".format(
                                     getVintelMap(),
                                     self.txtRegions.text()))
            self.txtRegions.setFocus()
            return False

        items = self.listRegion.selectedItems()
        litems = []
        for item in items:
            if len(item.text()) > 0:
                litems.append(item.text())
        save_cache = ",".join(litems)
        if self.txtRegions.text():
            save_cache += "," + self.txtRegions.text()
        # just to make sure
        save_cache = save_cache.lstrip(",")
        Cache().putIntoCache("region_name_range", save_cache, 60 * 60 * 24 * 365)
        self.new_region_range_chosen.emit(save_cache)

        return True

    def sound_setup(self):
        self.soundset = Cache().getFromCache("sound_setting_list")
        if self.soundset:
            self.soundset = literal_eval(self.soundset)
        if not self.soundset:
            self.soundset = []
            for dist in range(0, 6):
                entry = ["{} Jumps".format(dist), os.path.join(soundPath(), "alert.wav"), 25]
                self.soundset.append(entry)
            self.soundset.append(['KOS', os.path.join(soundPath(), "warning.wav"), 25])
            self.soundset.append(['Request', os.path.join(soundPath(), "request.wav"), 25])
        header = ["Trigger", "Sound-File", "Volume"]
        self.lstSound.setModel(self.SoundTableModel(self.soundset, header, self))
        self.lstSound.resizeColumnsToContents()
        # select whole row
        self.lstSound.setSelectionBehavior(QAbstractItemView.SelectRows)
        # only one at a time
        self.lstSound.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sound_data_changed = False
        self.sound_current_rowIndex = None
        self.orgVolume = SoundManager().soundVolume
        self.lstSound.clicked.connect(self.sound_row_clicked)
        self.sliderVolume.valueChanged.connect(self.sound_set_volume)
        self.txtSound.textChanged.connect(self.sound_set_file)
        self.btnSoundSearch.clicked.connect(self.sound_browse_file)
        self.btnPlay.clicked.connect(self.sound_play)

    def sound_row_clicked(self, rowIndex):
        model = rowIndex.model()
        self.sound_current_rowIndex = rowIndex
        self.txtSound.setText(model.getData(model.index(rowIndex.row(), 1)))
        self.sliderVolume.setValue(model.getData(model.index(rowIndex.row(), 2)))
        self.btnPlay.setEnabled(os.path.exists(self.txtSound.text()))

    def sound_set_volume(self, val):
        if self.sound_current_rowIndex:
            model = self.sound_current_rowIndex.model()
            row = self.sound_current_rowIndex.row()
            model.setData(model.index(row, 2), val)

    def sound_set_file(self, val):
        if self.sound_current_rowIndex:
            model = self.sound_current_rowIndex.model()
            row = self.sound_current_rowIndex.row()
            model.setData(model.index(row, 1), self.txtSound.text())
            self.btnPlay.setEnabled(os.path.exists(self.txtSound.text()))

    def sound_play(self):
        if self.sound_current_rowIndex:
            SoundManager().setSoundVolume(self.sliderVolume.value())
            SoundManager().playSoundFile(self.txtSound.text())
            SoundManager().setSoundVolume(self.orgVolume)

    def sound_browse_file(self):
        if self.sound_current_rowIndex:
            soundFile = self.txtSound.text()
            if not os.path.exists(soundFile):
                soundFile = os.path.join(soundPath(), os.path.basename(soundFile))
            file = QFileDialog.getOpenFileName(self, "Sound File", soundFile, "Sound Files (*.wav)")
            if file[0] != '':
                self.txtSound.setText(file[0])

    def map_add_color_row(self):
        index = self.tableViewMap.selectionModel().currentIndex()
        if index.isValid():
            self.tableViewMap.model().insertRows(index.row(), 1)

    def map_remove_color_row(self):
        index = self.tableViewMap.selectionModel().currentIndex()
        if index.isValid():
            self.tableViewMap.model().removeRows(index.row(), 1)

    def map_select_color(self, sQModelIndex: QModelIndex):
        if not sQModelIndex.isValid():
            return False
        if sQModelIndex.column() > 0:  # Color column
            color = stringToColor(sQModelIndex.data())
            color = dialogColor(color)
            if color.isValid():
                self.tableViewMap.model().setData(sQModelIndex, color.name(), Qt.EditRole)
                return True
            return False
        return False

    def set_map_table_model(self, index):
        # dirty... but somehow the Model doesn't update the dataset...
        self.mapColorList[
            self.cmbAlertType.itemText(self.mapColorIndex)] = self.model.m_grid_data.copy()
        self.mapColorIndex = index
        idx = self.cmbAlertType.itemText(index)
        # self.tableViewMap.model().submitAll()
        self.model = JsModel(self.mapColorList[idx], self.java_script.js_header)
        self.tableViewMap.setModel(self.model)

    def color_chooser(self):
        color = stringToColor(self.color)
        color = dialogColor(color)
        if color.isValid():
            self.color = color.name()

    def isInteger(self, value) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False

    def save_settings(self):
        if not self.region_save():
            return
        if not self.isInteger(self.txtJumpDistance.text()):
            self.txtJumpDistance.setFocus(Qt.OtherFocusReason)
            return
        self.settings_saved.emit()
        # dirty, but make sure the latest Model is copied to our data
        self.set_map_table_model(0)
        self.java_script.js_lst = self.mapColorList.copy()
        self.java_script.save_settings()
        mod = self.lstSound.model()
        sound_set = mod.getDataSet().copy()
        Cache().putIntoCache("sound_setting_list", str(sound_set))
        text = self.txtChatrooms.toPlainText()
        rooms = [name.strip() for name in text.split(",")]
        if u",".join(rooms) != Cache().getFromCache("room_names"):
            self.rooms_changed.emit(rooms)
        self.accept()

    def cancel_setting(self):
        self.reject()


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication
    from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QComboBox, QPushButton

    a = QApplication(sys.argv)
    d = SettingsDialog()
    d.show()
    sys.exit(a.exec_())
