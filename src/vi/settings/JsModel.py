#  Vintel - Visual Intel Chat Analyzer
#  Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant, pyqtSignal
from PyQt5.QtGui import QBrush, QFont
from PyQt5.QtWidgets import QTableView


class JsModel(QAbstractTableModel):
    m_gridData = []
    maxRows = 2
    maxCols = 3
    edit_complete = pyqtSignal(str)

    def __init__(self, parent=None):
        super(JsModel, self).__init__(parent)

    # resolve from dataset
    def rowCount(self, parent=None, *args, **kwargs):
        return 2

    # resolve from dataset
    def columnCount(self, parent=None, *args, **kwargs):
        return 3

    # Table-Column headers
    def headerData(self, section: int, Qt_Orientation, role=None):
        if role == Qt.DisplayRole and Qt_Orientation == Qt.Horizontal:
            if section == 0:
                return "first"
            if section == 1:
                return "second"
            if section == 2:
                return "third"
        return QVariant()

    # this returns the data to the Viewer
    def data(self, index: QModelIndex, role=None):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            if row == 0 and col == 1:
                return "<--left"
            if row == 1 and col == 1:
                return "right-->"
            return "Row%d, Column%d" % (index.row() + 1, index.column() + 1)
        elif role == Qt.FontRole:
            if row == 0 and col == 0:
                return QFont().setBold(True)
        elif role == Qt.BackgroundRole:
            if row == 1 and col == 2:
                return QBrush(Qt.red)
        elif role == Qt.TextAlignmentRole:
            if row == 1 and col == 1:
                return Qt.AlignRight + Qt.AlignVCenter
        elif role == Qt.CheckStateRole:
            if row == 1 and col == 0:
                return Qt.Checked
        return QVariant()

    """
    setData() will be called each time the user edits a cell. The index parameter tells us
    which field has been edited and value provides the result of the editing process. The role 
    will always be set to Qt::EditRole because our cells only contain text. If a checkbox
    were present and user permissions are set to allow the checkbox to be selected, calls 
    would also be made with the role set to Qt::CheckStateRole.
    """
    def setData(self, index: QModelIndex, data: QVariant, role: int=None):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            if index.row >= self.maxRows or index.column >= self.maxCols:
                return False
            self.m_gridData[row][col] = str(data)
            result = ""
            self.edit_complete.emit(result)
            return True
        return False

    """
    Various properties of a cell can be adjusted with flags().
    Returning Qt::ItemIsSelectable | Qt::ItemIsEditable | Qt::ItemIsEnabled is enough to show
    an editor that a cell can be selected.
    
    If editing one cell modifies more data than the data in that particular cell, the model
    must emit a dataChanged() signal in order for the data that has been changed to be read.
    """
    def flags(self, QModelIndex):
        return Qt.ItemIsEditable or super(JsModel, self).flags(QModelIndex)


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    tableView = QTableView()
    myModel = JsModel()
    tableView.setModel(myModel)
    tableView.show()
    a.exec_()
