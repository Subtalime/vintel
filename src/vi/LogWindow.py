from PyQt5 import QtWidgets, QtGui, QtCore
from .cache.cache import Cache
import logging
from vi.version import DISPLAY

class LogWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.setBaseSize(400, 300)
        # self.menubar = QtWidgets.QMenuBar(self)
        # self.menubar.setGeometry(QtCore.QRect(0, 0, 400, 21))
        # self.menu = QtWidgets.QMenu(self.menubar)
        # self.menu.setTitle("Level")
        # self.setMenuBar(self.menubar)
        # self.trace = QtWidgets.QAction(self)
        # self.trace.setCheckable(True)
        # self.trace.setChecked(False)
        # self.trace.setText("Trace")
        # self.debug = QtWidgets.QAction(self)
        # self.debug.setCheckable(True)
        # self.debug.setChecked(False)
        # self.debug.setText("Debug")
        # self.menu.addAction(self.trace)
        # self.menu.addAction(self.debug)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowTitle("{} Logging".format(DISPLAY))
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        self.setBaseSize(400,300)
        vbox.addWidget(self.textEdit)

        self.cache = Cache()
        rect = self.cache.getFromCache("log_window")
        if rect:
            self.restoreGeometry(rect)
        vis = self.cache.getFromCache("log_window_visible")
        if vis:
            self.show()
        mini = self.cache.getFromCache("log_window_minimized")
        if mini:
            self.setWindowState(QtCore.Qt.WindowMinimized)


    def write(self, text):
        self.textEdit.setFontWeight(QtGui.QFont.Normal)
        self.textEdit.append(text)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.cache.putIntoCache("log_window", bytes(self.saveGeometry()))
        self.cache.putIntoCache("log_window_visible", not self.isHidden())
        self.cache.putIntoCache("log_window_minimized", self.isMinimized())


class LogWindowHandler(logging.Handler):

    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent

    def emit(self, record):
        self.parent.write(self.format(record))
        self.parent.update()

