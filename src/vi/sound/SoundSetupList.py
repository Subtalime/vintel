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

import os
from ast import literal_eval
from PyQt5.QtCore import QAbstractTableModel, QVariant
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QFileDialog
from vi.ui.SoundSetupList import Ui_Dialog

from vi.sound.soundmanager import SoundManager
from vi.cache.cache import Cache
from vi.resources import soundPath, resourcePath

class SoundSettingDialog(QDialog, Ui_Dialog):

    class MyTableModel(QAbstractTableModel):
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

        def data(self, index, role = Qt.DisplayRole):
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
        QDialog.__init__(self,parent=parent)
        self.setupUi(self)
        # get Sounds from Cache
        self.soundset = Cache().getFromCache("sound_setting_list")
        if self.soundset:
            self.soundset = literal_eval(self.soundset)
        if not self.soundset:
            self.soundset = []
            for dist in range(0, 6):
                entry = ["{} Jumps".format(dist), os.path.join(resourcePath("vi/ui/res/"), "178032__zimbot__redalert-klaxon-sttos-recreated.wav"), 25]
                self.soundset.append(entry)
            self.soundset.append(['KOS', os.path.join(resourcePath("vi/ui/res"), "178031__zimbot__transporterstartbeep0-sttos-recreated.wav"), 25])
            self.soundset.append(['Request', os.path.join(resourcePath("vi/ui/res"), "178028__zimbot__bosun-whistle-sttos-recreated.wav"), 25])
        header = ["Trigger", "Sound-File", "Volume"]
        tblModel = self.MyTableModel(self.soundset, header, self)
        self.lstSound.setModel(tblModel)
        self.lstSound.resizeColumnsToContents()
        # select whole row
        self.lstSound.setSelectionBehavior(QAbstractItemView.SelectRows)
        # only one at a time
        self.lstSound.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lstSound.clicked.connect(self.rowClicked)
        self.data_changed = False
        self.current_rowIndex = None
        self.orgVolume = SoundManager().soundVolume
        self.volumeSlider.valueChanged.connect(self.setSoundVolume)
        self.txtSound.textChanged.connect(self.setSoundFile)
        self.buttonBox.accepted.connect(self.saveClicked)
        self.buttonBox.rejected.connect(self.reject)
        self.btnSearch.clicked.connect(self.browseFile)
        self.btnPlay.clicked.connect(self.playSound)

    def playSound(self):
        if self.current_rowIndex:
            SoundManager().setSoundVolume(self.volumeSlider.value())
            SoundManager().playSoundFile(self.txtSound.text())
            SoundManager().setSoundVolume(self.orgVolume)

    def browseFile(self):
        if self.current_rowIndex:
            import os
            soundFile = self.txtSound.text()
            if not os.path.exists(soundFile):
                soundFile = os.path.join(soundPath(), os.path.basename(soundFile))
            file = QFileDialog.getOpenFileName(self, "Sound File", soundFile, "Sound Files (*.wav)")
            if file[0] != '':
                self.txtSound.setText(file[0])

    def saveClicked(self):
        # get all the data from the view
        mod = self.lstSound.model()
        soundset = mod.getDataSet()
        Cache().putIntoCache("sound_setting_list", str(soundset))
        self.accept()

    def setSoundFile(self, val):
        if self.current_rowIndex:
            model = self.current_rowIndex.model()
            row = self.current_rowIndex.row()
            model.setData(model.index(row, 1), self.txtSound.text())

    def setSoundVolume(self, val):
        if self.current_rowIndex:
            model = self.current_rowIndex.model()
            row = self.current_rowIndex.row()
            model.setData(model.index(row, 2), self.volumeSlider.value())

    def rowClicked(self, rowIndex):
        model = rowIndex.model()
        self.current_rowIndex = rowIndex
        self.txtSound.setText(model.getData(model.index(rowIndex.row(), 1)))
        self.volumeSlider.setValue(model.getData(model.index(rowIndex.row(), 2)))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication([])
    SoundManager().soundActive = True
    SoundManager().soundThread.start()
    dia = SoundSettingDialog()
    dia.show()
    sys.exit(app.exec_())
