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

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import *

from vi.color.helpers import color_dialog, string_to_color
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.settings.SettingsFormTemplate import SettingsFormTemplate
from vi.states import State
from vi.ui.ColorForm import Ui_Form


class JsModel(QAbstractTableModel):
    def __init__(self, dataset=None, header=None):
        super(JsModel, self).__init__()
        self.m_grid_data = dataset
        self.m_header = header

    # resolve from dataset
    def rowCount(self, index=QModelIndex(), *args, **kwargs):
        length = len(self.m_grid_data)
        return length

    # resolve from dataset
    def columnCount(self, index=QModelIndex(), *args, **kwargs):
        length = len(self.m_grid_data[0])
        return length

    # Table-Column headers
    def headerData(
        self, column: int, orientation, role: int = Qt.DisplayRole
    ) -> QVariant:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return QVariant(self.m_header[column])
        return QVariant()

    def getData(self):
        return self.m_grid_data

    # this returns the data to the Viewer
    def data(self, index: QModelIndex, role=None):
        # if not index.isValid() or not (
        #         0 <= index.row() < self.rowCount() and 0 <= index.col() < self.columnCount()):
        #     return QVariant()
        #
        if (
            index.isValid()
            and 0 <= index.row() < self.rowCount()
            and 0 <= index.column() < self.columnCount()
        ):
            if role == Qt.DisplayRole:
                return self.m_grid_data[index.row()][index.column()]
            elif role == Qt.BackgroundRole:
                if index.column() == 1:
                    return QBrush(
                        string_to_color(self.m_grid_data[index.row()][index.column()])
                    )
            elif role == Qt.ForegroundRole:
                if index.column() == 1:
                    return QBrush(
                        string_to_color(
                            self.m_grid_data[index.row()][index.column() + 1]
                        )
                    )

        return QVariant()

    """
    setData() will be called each time the user edits a cell. The index parameter tells us
    which field has been edited and value provides the result of the editing process. The role 
    will always be set to Qt::EditRole because our cells only contain text. If a checkbox
    were present and user permissions are set to allow the checkbox to be selected, calls 
    would also be made with the role set to Qt::CheckStateRole.
    """

    def setData(self, index: QModelIndex, data: QVariant, role: int = Qt.EditRole):
        if role == Qt.EditRole and index.isValid():
            row = index.row()
            col = index.column()
            if (
                col > 0
                and str(data).startswith("#")
                and len(str(data)) == 7
                and QColor(data).isValid()
                or col == 0
                and 0 <= int(data) <= 86400
            ):
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

    def removeRows(
        self, position: int, rows: int = 1, parent=QModelIndex(), *args, **kwargs
    ):
        self.beginRemoveRows(parent, position, position + rows - 1)
        del self.m_grid_data[position : position + rows]
        self.endRemoveRows()
        return True

    def insertRows(
        self, position: int, rows: int = 1, parent=QModelIndex(), *args, **kwargs
    ):
        self.beginInsertRows(parent, position, position + rows - 1)
        for row in range(rows):
            self.m_grid_data.insert(position + 1 + row, [86400, "#ffffff", "#000000"])
        self.endInsertRows()
        return True

    def sort(self, column_number: int, order=None):
        if column_number != 0:
            return
        self.layoutAboutToBeChanged.emit()
        self.m_grid_data = sorted(
            self.m_grid_data, key=lambda operator: operator[column_number]
        )
        if order == Qt.DescendingOrder:
            self.m_grid_data.reverse()
        self.layoutChanged.emit()


class ColorForm(SettingsFormTemplate, Ui_Form):
    State_Index = [State["ALARM"], State["REQUEST"], State["CLEAR"]]

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.java_script = ColorJavaScript()
        self.current_index = 0
        self.model = JsModel(
            self.java_script.js_lst[self.State_Index[self.current_index]],
            self.java_script.js_header,
        )
        self.colorTable.setModel(self.model)
        self.colorTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.colorTable.resizeColumnsToContents()
        self.colorTable.setSortingEnabled(True)
        self.colorTable.sortByColumn(0, Qt.AscendingOrder)
        self.colorTable.doubleClicked.connect(self.select_color)
        self.colorTable.clicked.connect(self.select_color)
        self.colorType.addItems(self.java_script.get_keys())
        self.colorType.currentIndexChanged.connect(self.set_map_table_model)
        self.colorAddTime.clicked.connect(self.color_add_row)
        self.colorDelTime.clicked.connect(self.color_del_row)

    def color_add_row(self):
        index = self.colorTable.selectionModel().currentIndex()
        if index.isValid():
            self.model.insertRows(index.row(), 1)
            self.colorTable.setCurrentIndex(index)
        else:
            self.model.insertRows(self.model.rowCount(), 1)
            self.colorTable.setCurrentIndex(self.model.index(self.model.rowCount(), 0))
        self.change_detected()

    def color_del_row(self):
        index = self.colorTable.selectionModel().currentIndex()
        if index.isValid():
            self.model.removeRows(index.row(), 1)
            self.change_detected()

    def select_color(self, selected_index: QModelIndex):
        if not selected_index.isValid():
            return False
        if selected_index.column() > 0:  # Color column
            color = string_to_color(selected_index.data())
            color = color_dialog(color, parent=self)
            if color.isValid():
                self.model.setData(selected_index, color.name(), Qt.EditRole)
                self.change_detected()
                return True
            return False
        return True

    def set_map_table_model(self, index):
        self.java_script.js_lst[
            self.State_Index[self.current_index]
        ] = self.model.getData()
        self.model = JsModel(
            self.java_script.status_list(State[self.colorType.itemText(index)]),
            self.java_script.js_header,
        )
        self.colorTable.setModel(self.model)
        self.current_index = index

    @property
    def data_changed(self) -> bool:
        compare = ColorJavaScript()
        self.java_script.js_lst[
            self.State_Index[self.current_index]
        ] = self.model.getData()
        if self.java_script.js_lst != compare.js_lst:
            return True
        return False

    def save_data(self):
        self.java_script.save_settings()


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = ColorForm()
    d.show()
    sys.exit(a.exec_())
