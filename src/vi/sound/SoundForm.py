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

from PyQt5.QtCore import QModelIndex, QVariant, QAbstractTableModel, pyqtSignal, Qt
from PyQt5.QtWidgets import QFileDialog, QAbstractItemView
from PyQt5.QtGui import *

import os
from vi.ui.SoundForm import Ui_Form
from vi.settings.SettingsFormTemplate import SettingsFormTemplate
from vi.settings.settings import SoundSettings
from vi.resources import soundPath
from vi.sound.soundmanager import SoundManager


class SoundTableModel(QAbstractTableModel):
    layout_to_be_changed = pyqtSignal()
    layout_changed = pyqtSignal()

    def __init__(self, dataset: list = None, headerdata: list = None):
        """
        Args:
            dataset: a list of lists
            headerdata: a list of header strings
        """
        QAbstractTableModel.__init__(self)
        self.data_list = dataset
        self.headerdata = headerdata

    def rowCount(self, index=QModelIndex(), *args, **kwargs):
        return len(self.data_list)

    def columnCount(self, index=QModelIndex(), *args, **kwargs):
        if len(self.data_list) > 0:
            return len(self.data_list[0])
        return 0

    def data(self, index: QModelIndex, role=None) -> QVariant:
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.data_list[index.row()][index.column()])

    def setData(self, index: QModelIndex, value: QVariant, role: int = None) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        self.data_list[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
        return True

    def getDataSet(self):
        return self.data_list

    def getData(self, index: QModelIndex):
        if not index.isValid():
            return None
        return self.data_list[index.row()][index.column()]

    def getDataRow(self, row):
        return self.data_list[row]

    def headerData(
        self, column: int, Qt_Orientation, role: int = Qt.DisplayRole
    ) -> QVariant:
        if Qt_Orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[column])
        return QVariant()

    def sort(self, column_number: int, order: int = None):
        """
        Sort table by given column number.
        """
        self.layout_to_be_changed.emit()
        self.data_list = sorted(
            self.data_list, key=lambda operator: operator[column_number]
        )
        if order == Qt.DescendingOrder:
            self.data_list.reverse()
        self.layout_changed.emit()


class SoundForm(SettingsFormTemplate, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.sound_manager = SoundManager()
        self.sound_set = SoundSettings().sound
        header = ["Trigger", "Sound-File", "Volume"]
        self.model = SoundTableModel(self.sound_set, header)
        self.lstSound.setModel(self.model)
        self.lstSound.resizeColumnsToContents()
        # select whole row
        self.lstSound.setSelectionBehavior(QAbstractItemView.SelectRows)
        # only one at a time
        self.lstSound.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sound_data_changed = False
        self.current_row_index = None
        self.lstSound.clicked.connect(self.sound_row_clicked)
        self.sliderVolume.valueChanged.connect(self.sound_set_volume)
        self.txtSound.textChanged.connect(self.sound_set_file)
        self.btnSoundSearch.clicked.connect(self.sound_browse_file)
        self.btnPlay.clicked.connect(self.play)
        self.btnPlay.setEnabled(False)
        self.sliderVolume.setEnabled(False)

    def sound_row_clicked(self, row_index):
        self.current_row_index = row_index
        self.txtSound.setText(self.model.getData(self.model.index(row_index.row(), 1)))
        self.sliderVolume.setValue(
            self.model.getData(self.model.index(row_index.row(), 2))
        )
        self.btnPlay.setEnabled(os.path.exists(self.txtSound.text()))
        self.sliderVolume.setEnabled(os.path.exists(self.txtSound.text()))

    def sound_set_volume(self, val):
        if self.current_row_index:
            self.model.setData(
                self.model.index(self.current_row_index.row(), 2), val, role=Qt.EditRole
            )
            self.lstSound.setFocus()
            self.change_detected()

    def sound_set_file(self):
        if self.current_row_index:
            self.model.setData(
                self.model.index(self.current_row_index.row(), 1),
                self.txtSound.text(),
                role=Qt.EditRole,
            )
            self.btnPlay.setEnabled(os.path.exists(self.txtSound.text()))
            self.sliderVolume.setEnabled(os.path.exists(self.txtSound.text()))
            self.change_detected()

    def play(self):
        if self.current_row_index:
            # enable sound for this test
            preset = self.sound_manager.enable_sound
            self.sound_manager.enable_sound = True
            self.sound_manager.playSoundFile(
                self.txtSound.text(), self.sliderVolume.value()
            )
            self.sound_manager.enable_sound = preset
            self.lstSound.setFocus()

    def sound_browse_file(self):
        if self.current_row_index:
            sound_file = self.txtSound.text()
            if not os.path.exists(sound_file):
                sound_file = os.path.join(soundPath(), os.path.basename(sound_file))
            file = QFileDialog.getOpenFileName(
                self, "Sound File", sound_file, "Sound Files (*.wav)"
            )
            if file[0] != "":
                self.txtSound.setText(file[0])
                self.sound_set_file()

    def save_data(self):
        SoundSettings().sound = self.sound_set

    @property
    def data_changed(self) -> bool:
        return self.sound_set != SoundSettings().sound


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = SoundForm()
    d.show()
    sys.exit(a.exec_())
