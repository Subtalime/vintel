import os
import pickle
from ast import literal_eval
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QFileDialog
from PyQt5.QtCore import pyqtSignal, QModelIndex, Qt, QAbstractTableModel, QVariant
from vi.settings.JsModel import stringToColor, dialogColor, JsModel
from vi.dotlan.javascript import JavaScript
from vi.ui.Settings import Ui_Dialog
from vi.cache.cache import Cache
from vi.resources import soundPath
from vi.sound.soundmanager import SoundManager

class SettingsDialog(QDialog, Ui_Dialog):
    settings_saved = pyqtSignal()

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
        self.java_script = JavaScript()
        self.mapColorList = self.java_script.js_lst.copy()
        self.mapColorIndex = 0
        self.model = JsModel(self.mapColorList['Alarm'], self.java_script.js_header)
        self.tableViewMap.setModel(self.model)
        self.tableViewMap.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableViewMap.resizeColumnsToContents()
        self.tableViewMap.setSortingEnabled(True)
        self.tableViewMap.sortByColumn(0, Qt.AscendingOrder)
        self.tableViewMap.doubleClicked.connect(self.mapSelectColor)
        self.tableViewMap.clicked.connect(self.mapSelectColor)
        self.cmbAlertType.addItems(self.mapColorList.keys())
        self.cmbAlertType.currentIndexChanged.connect(self.setTableModel)
        self.btnMapAddTime.clicked.connect(self.addMapColorRow)
        self.btnMapDelTime.clicked.connect(self.removeMapColorRow)
        # all General settings
        self.btnColor.clicked.connect(self.colorChooser)
        self.buttonBox.accepted.connect(self.saveSettings)
        self.buttonBox.rejected.connect(self.reject)
        self.txtKosInterval.setEnabled(False)
        # all Sound Settings
        self.setupSound()

    def setupSound(self):
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
        self.lstSound.clicked.connect(self.soundRowClicked)
        self.sliderVolume.valueChanged.connect(self.setSoundVolume)
        self.txtSound.textChanged.connect(self.setSoundFile)
        self.btnSoundSearch.clicked.connect(self.browseSoundFile)
        self.btnPlay.clicked.connect(self.playSound)

    def soundRowClicked(self, rowIndex):
        model = rowIndex.model()
        self.current_rowIndex = rowIndex
        self.txtSound.setText(model.getData(model.index(rowIndex.row(), 1)))
        self.sliderVolume.setValue(model.getData(model.index(rowIndex.row(), 2)))
        self.btnPlay.setEnabled(os.path.exists(self.txtSound.text()))


    def setSoundVolume(self, val):
        if self.current_rowIndex:
            model = self.current_rowIndex.model()
            row = self.current_rowIndex.row()
            model.setData(model.index(row, 2), val)

    def setSoundFile(self, val):
        if self.current_rowIndex:
            model = self.current_rowIndex.model()
            row = self.current_rowIndex.row()
            model.setData(model.index(row, 1), self.txtSound.text())
            self.btnPlay.setEnabled(os.path.exists(self.txtSound.text()))

    def playSound(self):
        if self.sound_current_rowIndex:
            SoundManager().setSoundVolume(self.sliderVolume.value())
            SoundManager().playSoundFile(self.txtSound.text())
            SoundManager().setSoundVolume(self.orgVolume)

    def browseSoundFile(self):
        if self.current_rowIndex:
            soundFile = self.txtSound.text()
            if not os.path.exists(soundFile):
                soundFile = os.path.join(soundPath(), os.path.basename(soundFile))
            file = QFileDialog.getOpenFileName(self, "Sound File", soundFile, "Sound Files (*.wav)")
            if file[0] != '':
                self.txtSound.setText(file[0])


    def addMapColorRow(self):
        index = self.tableViewMap.selectionModel().currentIndex()
        if index.isValid():
            self.tableViewMap.model().insertRows(index.row(), 1)

    def removeMapColorRow(self):
        index = self.tableViewMap.selectionModel().currentIndex()
        if index.isValid():
            self.tableViewMap.model().removeRows(index.row(), 1)


    def mapSelectColor(self, sQModelIndex: QModelIndex):
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

    def setTableModel(self, index):
        # dirty... but somehow the Model doesn't update the dataset...
        self.mapColorList[self.cmbAlertType.itemText(self.mapColorIndex)] = self.model.m_grid_data
        self.mapColorIndex = index
        idx = self.cmbAlertType.itemText(index)
        # self.tableViewMap.model().submitAll()
        self.model = JsModel(self.mapColorList[idx], self.java_script.js_header)
        self.tableViewMap.setModel(self.model)

    def colorChooser(self):
        color = stringToColor(self.color)
        color = dialogColor(color)
        if color.isValid():
            self.color = color.name()

    def saveSettings(self):
        self.settings_saved.emit()
        # make sure the latest Model is copied to our data
        self.setTableModel(0)
        self.java_script.js_lst = self.mapColorList.copy()
        self.java_script.save_settings()
        mod = self.lstSound.model()
        soundset = mod.getDataSet().copy()
        Cache().putIntoCache("sound_setting_list", str(soundset))
        self.accept()

if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication
    from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QComboBox, QPushButton
    string = JavaScript().getJs()
    a = QApplication(sys.argv)
    d = SettingsDialog()
    d.show()
    sys.exit(a.exec_())
