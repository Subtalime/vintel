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
from PyQt5 import QtCore, QtWidgets
import logging
from vi.logger import LogWindow, LogQueueHandler


class Main(QtWidgets.QMainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setObjectName("MainWindow")
        self.resize(1363, 904)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.setCentralWidget(self.centralwidget)
        self.mapbuttonwidget = QtWidgets.QWidget(self.centralwidget)
        self.mapbuttonwidget.setMinimumSize(QtCore.QSize(0, 24))
        self.mapbuttonwidget.setBaseSize(QtCore.QSize(1024, 0))
        self.mapbuttonwidget.setObjectName("mapbuttonwidget")
        self.frameButton = QtWidgets.QPushButton(self.mapbuttonwidget)
        self.frameButton.setMaximumSize(QtCore.QSize(16777215, 19))
        self.frameButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.frameButton.setObjectName("frameButton")
        self.zoomInButton = QtWidgets.QPushButton(self.mapbuttonwidget)
        self.zoomInButton.setMaximumSize(QtCore.QSize(16777215, 19))
        self.zoomInButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.zoomInButton.setObjectName("zoomInButton")


class Testing:
    def __init__(self):
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.addHandler(logging.StreamHandler(sys.stdout))
        self.LOGGER.setLevel(logging.DEBUG)

    def test(self):
        self.LOGGER.warning("testing warning")


if __name__ == "__main__":
    import sys
    from PyQt5.Qt import QApplication

    LOGGER = logging.getLogger()
    LOGGER.setLevel(logging.DEBUG)
    h = logging.StreamHandler(sys.stdout)
    LOGGER.addHandler(h)

    a = QApplication(sys.argv)
    # m = Main()
    # m.show()
    d = LogWindow()
    q = LogQueueHandler([d,])
    # LOGGER.addHandler(q)
    d.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, True)
    d.get_handler().setLevel(logging.DEBUG)
    d.show()
    LOGGER.debug("Test 1... now setting to INFO")
    d.show()
    LOGGER.info("Info Test 2 (should not be seen in Log-Window")
    t = Testing()
    t.test()
    a.exec_()
    # sys.exit(a.exec_())
