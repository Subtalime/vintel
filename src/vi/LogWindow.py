from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import pyqtSignal
from .cache.cache import Cache
import logging
from vi.version import DISPLAY

class LogWindow(QtWidgets.QWidget):
    logging_level_event = pyqtSignal(int)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        logHandler = LogWindowHandler(self)
        logging.getLogger().addHandler(logHandler)

        self.setBaseSize(400, 300)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setTitle()
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.textEdit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.textEdit.customContextMenuRequested.connect(self.contextMenuEvent)

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

    def setTitle(self):
        self.setWindowTitle("{} Logging ({})".format(DISPLAY, logging._levelToName[logging.getLogger().getEffectiveLevel()]))

    def write(self, text):
        self.textEdit.setFontWeight(QtGui.QFont.Normal)
        self.textEdit.append(text)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.cache.putIntoCache("log_window", bytes(self.saveGeometry()))
        self.cache.putIntoCache("log_window_visible", not self.isHidden())
        self.cache.putIntoCache("log_window_minimized", self.isMinimized())

    # popup to set Log-Level
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        logLevel = Cache().getFromCache("logging_level")
        if not logLevel:
            logLevel = logging.WARN
        currLevel = logging.getLogger().getEffectiveLevel()
        menu = QMenu(self)
        debug = QtWidgets.QAction("Debug", checkable=True)
        if currLevel == logging.DEBUG:
            debug.setChecked(True)
        menu.addAction(debug)
        info = QtWidgets.QAction("Info", checkable=True)
        if currLevel == logging.INFO:
            info.setChecked(True)
        menu.addAction(info)
        warning = QtWidgets.QAction("Warning", checkable=True)
        if currLevel == logging.WARN:
            warning.setChecked(True)
        menu.addAction(warning)
        error = QtWidgets.QAction("Error", checkable=True)
        if currLevel == logging.ERROR:
            error.setChecked(True)
        menu.addAction(error)
        crit = QtWidgets.QAction("Critical", checkable=True)
        if currLevel == logging.CRITICAL:
            crit.setChecked(True)
        menu.addAction(crit)
        setting = menu.exec_(self.mapToGlobal(event))
        if setting == debug:
            logLevel = logging.DEBUG
        elif setting == info:
            logLevel = logging.INFO
        elif setting == warning:
            logLevel = logging.WARN
        elif setting == error:
            logLevel = logging.ERROR
        elif setting == crit:
            logLevel = logging.CRITICAL
        logging.getLogger().setLevel(logLevel)
        Cache().putIntoCache("logging_level", logLevel)
        self.setTitle()
        self.logging_level_event.emit(logLevel)

class LogWindowHandler(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent
        formatter = logging.Formatter('%(asctime)s|%(levelname)s: %(message)s', datefmt='%I:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record):
        self.parent.write(self.format(record))
        self.parent.update()
