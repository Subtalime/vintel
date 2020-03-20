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
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QColorDialog


def stringToColor(sQColor: str = None) -> QColor:
    if str(sQColor).startswith("#"):
        color = str(sQColor).lstrip("#")
        lv = len(color)
        cs = tuple(int(color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    else:
        cs = [0, 0, 0]
    return QColor(cs[0], cs[1], cs[2])


def dialogColor(color=QColor()):
    return QColorDialog().getColor(initial=color)


class JsModel(QAbstractTableModel):

    def __init__(self, dataset=None, header=None):
        super(JsModel, self).__init__()
        self.m_grid_data = dataset
        self.m_header = header

    # resolve from dataset
    def rowCount(self, index=QModelIndex(), *args, **kwargs):
        if index.isValid():
            return 0
        length = len(self.m_grid_data)
        return length

    # resolve from dataset
    def columnCount(self, index=QModelIndex(), *args, **kwargs):
        if index.isValid():
            return 0

        length = len(self.m_grid_data[0])
        return length

    # Table-Column headers
    def headerData(self, column: int, Qt_Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and Qt_Orientation == Qt.Horizontal:
            return QVariant(self.m_header[column])
        return QVariant()

    # this returns the data to the Viewer
    def data(self, index: QModelIndex, role=None):
        if not index.isValid() or not (
                0 <= index.row() < self.rowCount() and 0 <= index.column() < self.columnCount()):
            return QVariant()

        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            data = self.m_grid_data[row][col]
            return data
        elif role == Qt.BackgroundRole:
            if col == 1:
                qColor = stringToColor(self.m_grid_data[row][col])
                return QBrush(qColor)
        elif role == Qt.ForegroundRole:
            if col == 1:
                qColor = stringToColor(self.m_grid_data[row][col+1])
                return QBrush(qColor)

        return QVariant()

    """
    setData() will be called each time the user edits a cell. The index parameter tells us
    which field has been edited and value provides the result of the editing process. The role 
    will always be set to Qt::EditRole because our cells only contain text. If a checkbox
    were present and user permissions are set to allow the checkbox to be selected, calls 
    would also be made with the role set to Qt::CheckStateRole.
    """
    def setData(self, index: QModelIndex, data: QVariant, role: int = None):
        if role == Qt.EditRole and index.isValid():
            row = index.row()
            col = index.column()
            if col > 0 and str(data).startswith("#") and len(str(data)) == 7 and QColor(
                    data).isValid() or col == 0 and  0 <= int(data) <= 86400:
                self.m_grid_data[row][col] = str(data)
                self.dataChanged.emit(index, index, (Qt.DisplayRole,))
                return True
        return False

    """
    Various properties of a cell can be adjusted with flags().
    Returning Qt::ItemIsSelectable | Qt::ItemIsEditable | Qt::ItemIsEnabled is enough to show
    an editor that a cell can be selected.
    
    If editing one cell modifies more data than the data in that particular cell, the model
    must emit a dataChanged() signal in order for the data that has been changed to be read.
    """
    def flags(self, flags: QModelIndex):
        fl = super(self.__class__, self).flags(flags)
        fl |= Qt.ItemIsEditable
        fl |= Qt.ItemIsSelectable
        # fl |= Qt.ItemIsEnabled
        # fl |= Qt.ItemIsUserCheckable
        return fl

    def removeRows(self, position: int, rows: int = 1, parent=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, position, position+rows-1)
        del self.m_grid_data[position:position+rows]
        self.endRemoveRows()
        return True

    def insertRows(self, position: int, rows: int = 1, parent=QModelIndex(), *args, **kwargs):
        self.beginInsertRows(parent, position, position+rows-1)
        for row in range(rows):
            self.m_grid_data.insert(position + 1 + row, [86400, "#ffffff", "#000000"])
        self.endInsertRows()
        return True

    def sort(self, Ncol: int, order=None):
        if Ncol != 0:
            return
        self.layoutAboutToBeChanged.emit()
        self.m_grid_data = sorted(self.m_grid_data, key=lambda operator: operator[Ncol])
        if order == Qt.DescendingOrder:
            self.m_grid_data.reverse()
        self.layoutChanged.emit()


class JsTableView(QTableView):
    def __init__(self, parent=None, dataset=None, headerset=None):
        super(JsTableView, self).__init__(parent)
        if dataset and headerset:
            self.setModel(JsModel(dataset, headerset))
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        self.doubleClicked.connect(self.fn_clickAction)
        self.clicked.connect(self.fn_clickAction)

    def addRow(self):
        index = self.selectionModel().currentIndex()
        if index.isValid():
            self.model().insertRows(index.row())

    def deleteRow(self):
        index = self.selectionModel().currentIndex()
        if index.isValid():
            self.model().removeRows(index.row())

    def fn_clickAction(self, sQModelIndex: QModelIndex):
        if not sQModelIndex.isValid():
            return False
        if sQModelIndex.column() > 0:  # Color column
            color = stringToColor(sQModelIndex.data())
            color = dialogColor(color)
            if color.isValid():
                self.model().setData(sQModelIndex, color.name(), Qt.EditRole)
                return True
            return False
        return True


if __name__ == "__main__":
    def setTableModel(index):
        idx = combo.itemText(index)
        tableView.setModel(JsModel(js_lst[idx], js_header))
    def addRow():
        tableView.addRow()
    def remRow():
        tableView.deleteRow()

    import sys
    from PyQt5.Qt import QApplication
    from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QComboBox, QPushButton

    ALARM_COLORS = [[60 * 4, "#FF0000", "#FFFFFF"], [60 * 10, "#FF9B0F", "#000000"],
                    [60 * 15, "#FFFA0F", "#000000"], [60 * 25, "#FFFDA2", "#000000"],
                    [60 * 60 * 24, "#FFFFFF", "#000000"]]
    REQUEST_COLORS = [[60 * 2, "#ffaaff", "#000000"],
                      [60 * 60 * 24, "#FFFFFF", "#000000"]]
    CLEAR_COLORS = [[60 * 2, "#59FF6C", "#000000"],
                    [60 * 60 * 24, "#FFFFFF", "#000000"]]
    js_lst = {"Alarm": ALARM_COLORS, "Request": REQUEST_COLORS, "Clear": CLEAR_COLORS}
    js_header = ["Duration", "Background", "Text"]
    a = QApplication(sys.argv)

    main = QWidget()
    main.resize(400, 400)
    layout = QVBoxLayout()
    combo = QComboBox()
    combo.addItems(js_lst.keys())
    combo.currentIndexChanged.connect(setTableModel)
    tableView = JsTableView(dataset=js_lst[combo.currentText()], headerset=js_header)
    buttadd = QPushButton("Add Row")
    buttadd.clicked.connect(addRow)
    buttrem = QPushButton("Delete Row")
    buttrem.clicked.connect(remRow)
    layout.addWidget(combo)
    layout.addWidget(tableView)
    layout.addWidget(buttadd)
    layout.addWidget(buttrem)
    main.setLayout(layout)
    main.show()
    # tableView.show()
    sys.exit(a.exec_())
