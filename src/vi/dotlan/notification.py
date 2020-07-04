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
from PyQt5.QtWidgets import (
    QTableView,
    QAbstractItemView,
)
from PyQt5.QtCore import QAbstractTableModel, QVariant, pyqtSignal, Qt
from vi.cache.cache import Cache
import pickle


class Notification:
    def __init__(
        self, duration: int = None, color_background: str = None, color_text: str = None
    ):
        self.duration = duration
        self.background = color_background
        self.text = color_text

    def __repr__(self):
        return "{},'{}','{}'".format(self.duration, self.background, self.text)


def _sortTime(item: Notification):
    return item.duration


class Notifications:
    def __init__(self, notification_name: str):
        self.name = notification_name.upper()
        self.notifications = []

    def load(self):
        self.notifications = pickle.loads(
            Cache().fetch("{}_notifications".format(self.name), True)
        )

    def add(self, notification: Notification):
        self.remove(notification.duration)
        self.notifications.append(notification)

    def remove(self, time: int):
        for item in self.notifications:
            if time == item.duration:
                self.notifications.remove(item)

    def save(self):
        Cache().put(
            "{}_notifications".format(self.name), pickle.dumps(self.notifications)
        )

    def __repr__(self):
        ret = "{}_COLORS = [".format(self.name)
        self.notifications.sort(key=_sortTime)
        for item in self.notifications:
            ret += str(item) + ","
        return ret.rstrip(",") + "]"


class NotificationsTableView(QTableView):
    class MyTableModel(QAbstractTableModel):
        layout_to_be_changed = pyqtSignal()
        layout_changed = pyqtSignal()
        data_changed = pyqtSignal(int, int)

        def __init__(self, datain, headerdata, parent=None):
            """
            Args:
                datain: a list of lists\n
                headerdata: a list of strings
            """
            QAbstractTableModel.__init__(self, parent)
            self.array_data = datain
            self.headerdata = headerdata

        def rowCount(self, parent=None):
            return len(self.array_data)

        def columnCount(self, parent=None):
            if len(self.array_data) > 0:
                return len(self.array_data[0])
            return 0

        def data(self, index, role=Qt.DisplayRole):
            if not index.isValid():
                return QVariant()
            elif role != Qt.DisplayRole:
                return QVariant()
            return QVariant(self.array_data[index.row()][index.column()])

        def setData(self, index, value, role=Qt.EditRole):
            if not index.isValid():
                return False
            if role != Qt.EditRole:
                return False
            self.array_data[index.row()][index.column()] = value
            self.data_changed.emit(index.row(), index.column())
            return True

        def getDataSet(self):
            return self.array_data

        def getData(self, index):
            if not index.isValid():
                return None
            return self.array_data[index.row()][index.column()]

        def getDataRow(self, row):
            return self.array_data[row]

        def headerData(self, col: object, orientation: object, role: object) -> object:
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return QVariant(self.headerdata[col])
            return QVariant()

        def sort(self, ncol: object, order: object) -> object:
            """
            Sort table by given column number.
            """
            self.layout_to_be_changed.emit()
            self.array_data = sorted(self.array_data, key=lambda operator: operator[ncol])
            if order == Qt.DescendingOrder:
                self.array_data.reverse()
            self.layout_changed.emit()

    def __init__(self, notification_set: Notifications):
        super().__init__()
        self.data = notification_set
        header = ["Duration", "Background-Color", "Text-Color"]
        self.setModel(self.MyTableModel(self.data.notifications, header, self))
        self.resizeColumnsToContents()
        # whole row selection
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        # only one at a time
        self.setSelectionMode(QAbstractItemView.SingleSelection)


if __name__ == "__main__":
    a = Notifications("alarm")
    for t in range(60, 600, 60):
        a.add(Notification(t, "#123456", "#654321"))

    print(a)
    a.save()
    a = Notifications("alarm")
    a.load()
    print(a)
