from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QColorDialog, QAbstractItemView
from PyQt5.QtCore import pyqtSignal, QModelIndex, Qt
from vi.settings.JsModel import JsTableView, stringToColor, dialogColor, JsModel
from vi.dotlan.javascript import JavaScript
from vi.ui.Settings import Ui_Dialog
from vi.cache.cache import Cache


class SettingsDialog(QDialog, Ui_Dialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.color = None
        self.setWindowTitle("Vintel Settings")
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
        self.btnColor.clicked.connect(self.colorChooser)
        self.buttonBox.accepted.connect(self.saveSettings)
        self.buttonBox.rejected.connect(self.reject)
        self.txtKosInterval.setEnabled(False)

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
        self.accept()

if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication
    from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QComboBox, QPushButton

    a = QApplication(sys.argv)
    d = SettingsDialog()
    d.show()
    sys.exit(a.exec_())
