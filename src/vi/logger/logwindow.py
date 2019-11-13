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

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import pyqtSignal, QEvent, Qt, QObject
from vi.cache.cache import Cache
import logging
import queue
from logging.handlers import QueueHandler, QueueListener
from time import time
from logging import LogRecord
from vi.version import DISPLAY

LOGGER = logging.getLogger(__name__)


class LogWindow(QtWidgets.QWidget):
    logging_level_event = pyqtSignal(int)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.logLevel = Cache().getFromCache("log_window_level")
        if not self.logLevel:
            # by default, have warnings only shown there
            self.logLevel = logging.WARNING
        # setup a blocking Queue (ready for tidying)
        self.queue = queue.Queue(-1)  # unlimited
        self.queue_handler = QueueHandler(self.queue)
        self.logHandler = LogWindowHandler(self)
        self.queue_listener = QueueListener(self.queue, self.logHandler)
        logging.getLogger().addHandler(self.queue_handler)
        self.logHandler.new_message.connect(self.store)
        # logging.getLogger().addHandler(self.logHandler)
        # keep maximum of 5k lines in buffer
        self.tidySize = 100
        self.pruneTime = time()
        # check only every hour
        self.pruneDelay = 60 * 5  # 1 hour
        self.doTidy = True
        self.log_records = []
        self._tidying = False
        self.setBaseSize(400, 300)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setTitle()
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse or QtCore.Qt.TextBrowserInteraction)
        self.textEdit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.textEdit.customContextMenuRequested.connect(self.contextMenuEvent)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        self.setBaseSize(400, 300)
        vbox.addWidget(self.textEdit)

        self.queue_listener.start()
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
        # stop adding records while Tidyup
        while self._tidying:
            continue
        self.log_records.append(record)
        if record.levelno >= self.logLevel:
            self.write(self.logHandler.format(record))
        if self.doTidy:
            if self.pruneTime + self.pruneDelay < time() and not self._tidying:
                num_records = len(self.log_records)
                if num_records > self.tidySize:
                    try:
                        self._tidying = True
                        LOGGER.debug("LogWindow Tidy start")
                        del self.log_records[:num_records - self.tidySize]
                    except Exception:
                        LOGGER.error("Error in Tidy-Up of Log-Window")
                    finally:
                        self._tidying = False
                        self.pruneTime = time()
                        self.refresh()
                        LOGGER.debug("LogWindow Tidy complete")

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
                LOGGER.debug("LogWindow hidden")
                self.hide()
            else:
                LOGGER.debug("LogWindow visible")
                self.show()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.cache.putIntoCache("log_window", bytes(self.saveGeometry()))
        self.cache.putIntoCache("log_window_visible", not self.isHidden())
        LOGGER.debug("LogWindow closed")
        self.queue_listener.stop()

    class MyAction(QtWidgets.QAction):
        def __init__(self, *args):
            QtWidgets.QAction.__init__(self, *args)
            self.setCheckable(True)

    # popup to set Log-Level
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        currLevel = self.logLevel
        menu = QMenu(self)
        debug = self.MyAction("Debug")
        if currLevel == logging.DEBUG:
            debug.setChecked(True)
        menu.addAction(debug)
        info = self.MyAction("Info")
        if currLevel == logging.INFO:
            info.setChecked(True)
        menu.addAction(info)
        warning = self.MyAction("Warning")
        if currLevel == logging.WARN:
            warning.setChecked(True)
        menu.addAction(warning)
        error = self.MyAction("Error")
        if currLevel == logging.ERROR:
            error.setChecked(True)
        menu.addAction(error)
        crit = self.MyAction("Critical")
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

        # self maybe not... so we can hold ALL data and filter the output based on Level?
        # self.logHandler.setLevel(self.logLevel)
        Cache().putIntoCache("log_window_level", self.logLevel)
        self.setTitle()
        self.logging_level_event.emit(self.logLevel)


class LogWindowHandler(logging.Handler, QObject):
    new_message = pyqtSignal(logging.LogRecord)

    def __init__(self, parent):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.parent = parent
        formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt='%H:%M:%S')
        # always log all messages ! The Window-Output is managed by self.logLevel
        self.setLevel(logging.DEBUG)
        self.setFormatter(formatter)

    def emit(self, record):
        self.new_message.emit(record)
