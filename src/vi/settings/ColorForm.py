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

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from vi.settings.JsModel import color_dialog, JsModel, string_to_color
from vi.dotlan.colorjavascript import ColorJavaScript
from vi.settings.SettingsFormTemplate import SettingsFormTemplate
from vi.states import State
from vi.ui.ColorForm import Ui_Form


class ColorForm(SettingsFormTemplate, Ui_Form):
    State_Index = [State['ALARM'], State['REQUEST'], State['CLEAR']]
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.java_script = ColorJavaScript()
        self.current_index = 0
        self.model = JsModel(self.java_script.js_lst[self.State_Index[self.current_index]], self.java_script.js_header)
        # self.model = JsModel(self.java_script.status_list(State['ALARM']), self.java_script.js_header)
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
            color = color_dialog(color)
            if color.isValid():
                self.model.setData(selected_index, color.name(), Qt.EditRole)
                self.change_detected()
                return True
            return False
        return True

    def set_map_table_model(self, index):
        self.java_script.js_lst[self.State_Index[self.current_index]] = self.model.getData()
        self.model = JsModel(self.java_script.status_list(State[self.colorType.itemText(index)]), self.java_script.js_header)
        self.colorTable.setModel(self.model)
        self.current_index = index

    @property
    def data_changed(self) -> bool:
        compare = ColorJavaScript()
        self.java_script.js_lst[self.State_Index[self.current_index]] = self.model.getData()
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
