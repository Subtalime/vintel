from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import pyqtSignal, QEvent, Qt
from .cache.cache import Cache
import logging
from logging import LogRecord
from vi.version import DISPLAY

# TODO: default to Logging.DEBUG, but filter output here to what is wanted
# TODO: go back in the Log (File?) and show based on Log-Setting
# TODO: prun Text-Size... may grow beyond X MB
class LogWindow(QtWidgets.QWidget):
    logging_level_event = pyqtSignal(int)
    log_records = []
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.logLevel = Cache().getFromCache("log_window_level")
        if not self.logLevel:
            # by default, have warnings only shown there
            self.logLevel = logging.WARNING
        self.logHandler = LogWindowHandler(self)
        self.logHandler.setLevel(self.logLevel)
        logging.getLogger().addHandler(self.logHandler)

        self.setBaseSize(400, 300)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setTitle()
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse or QtCore.Qt.TextBrowserInteraction)
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
        if bool(vis):
            self.show()

    def setTitle(self):
        self.setWindowTitle("{} Logging ({})".format(DISPLAY, logging._levelToName[self.logLevel]))

    def write(self, text):
        self.textEdit.setFontWeight(QtGui.QFont.Normal)
        self.textEdit.append(text)

    def store(self, record: LogRecord):
        self.log_records.append(record)
        if record.levelno >= self.logLevel:
            self.write(self.logHandler.format(record))

    def refresh(self):
        self.textEdit.clear()
        for record in self.log_records:
            if record.levelno >= self.logLevel:
                self.write(self.logHandler.format(record))
        self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super(LogWindow, self).resizeEvent(event)
        self.cache.putIntoCache("log_window", bytes(self.saveGeometry()))

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super(LogWindow, self).changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                self.cache.putIntoCache("log_window", bytes(self.saveGeometry()))
                self.cache.putIntoCache("log_window_visible", str(False))
                self.hide()
            else:
                self.show()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.cache.putIntoCache("log_window", bytes(self.saveGeometry()))
        self.cache.putIntoCache("log_window_visible", not self.isHidden())

    # popup to set Log-Level
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        currLevel = self.logLevel
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
        menu.addSeparator()
        clear = QtWidgets.QAction("Clear Log-Window")
        menu.addAction(clear)
        setting = menu.exec_(self.mapToGlobal(event))
        if setting == debug:
            currLevel = logging.DEBUG
        elif setting == info:
            currLevel = logging.INFO
        elif setting == warning:
            currLevel = logging.WARN
        elif setting == error:
            currLevel = logging.ERROR
        elif setting == crit:
            currLevel = logging.CRITICAL
        elif setting == clear:
            self.textEdit.clear()
        if self.logLevel != currLevel:
            self.logLevel = currLevel
            self.refresh()

        #self maybe not... so we can hold ALL data and filter the output based on Level?
        # self.logHandler.setLevel(self.logLevel)
        Cache().putIntoCache("log_window_level", self.logLevel)
        self.setTitle()
        self.logging_level_event.emit(self.logLevel)

class LogWindowHandler(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent
        formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt='%H:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record):
        self.parent.store(record)
        # self.parent.write(self.format(record))
        self.parent.update()
