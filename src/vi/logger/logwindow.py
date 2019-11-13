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

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import pyqtSignal, QEvent, Qt, QObject
from vi.cache.cache import Cache
import logging
import queue
import threading
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from time import time
from logging import LogRecord
from vi.version import DISPLAY

LOGGER = logging.getLogger(__name__)

_lock = threading.RLock()


def _acquireLock():
    """
    Acquire the module-level lock for serializing access to shared data.
    This should be released with _releaseLock().
    """
    if _lock:
        _lock.acquire()


def _releaseLock():
    """
    Release the module-level lock acquired by calling _acquireLock().
    """
    if _lock:
        _lock.release()


class LogWindow(QtWidgets.QWidget):
    """
    Output-Window of all Log-File-Content. More convenient than "tail -F" on the Log-File
    Also, ability to Filter by Log-Level
    """
    logging_level_event = pyqtSignal(int)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.cache = Cache()
        # setup a blocking Queue in case LogWindow can't keep up
        msg_queue = queue.Queue(-1)  # unlimited
        queue_handler = QueueHandler(msg_queue)
        # all done, now create new Handler
        logging.getLogger().addHandler(queue_handler)
        # our own Log-Handler
        self.logHandler = LogWindowHandler(self)
        # the queue will send to Log-Window-Handler
        self.queue_listener = QueueListener(msg_queue, self.logHandler)
        # any new Log-Messages, send to storage
        self.logHandler.new_message.connect(self.store)
        # keep maximum of 5k lines in buffer
        self.tidySize = 5000
        self.pruneTime = time()
        self._tidying = False
        # check only every hour
        self.pruneDelay = 60 * 60  # 1 hour
        # Log-Messages stored here
        self.log_records = []

        # oh, now actually build the window...
        self.setBaseSize(400, 300)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
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

        # start the Log-Queue
        self.queue_listener.start()
        self.logLevel = self.cache.getFromCache("log_window_level")
        if not self.logLevel:
            # by default, have warnings only shown here
            self.logLevel = logging.WARNING
        self.setTitle()

        rect = self.cache.getFromCache("log_window")
        if rect:
            self.restoreGeometry(rect)
        vis = self.cache.getFromCache("log_window_visible")
        if bool(vis):
            self.show()

    def setTitle(self):
        self.setWindowTitle("{} Logging ({})".format(DISPLAY, logging.getLevelName(self.logLevel)))

    def write(self, text):
        self.textEdit.setFontWeight(QtGui.QFont.Normal)
        self.textEdit.append(text)

    def prune(self):
        if not self._tidying and self.pruneTime + self.pruneDelay < time():
            self.pruneTime = time()
            num_records = len(self.log_records)
            if num_records > self.tidySize:
                try:
                    _acquireLock()
                    self._tidying = True
                    LOGGER.debug("LogWindow Tidy-Up start")
                    del self.log_records[:num_records - self.tidySize]
                except Exception as e:
                    LOGGER.error("Error in Tidy-Up of Log-Window", e)
                finally:
                    _releaseLock()
                    self._tidying = False
                    self.refresh()
                    LOGGER.debug("LogWindow Tidy-Up complete")

    def store(self, record: LogRecord):
        self.log_records.append(record)
        if record.levelno >= self.logLevel:
            self.write(self.logHandler.format(record))
        self.prune()

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

    # default QAction to make "checkable"
    class LogAction(QtWidgets.QAction):
        def __init__(self, name: str = None):
            QtWidgets.QAction.__init__(self, name)
            self.setCheckable(True)

    # popup to set Log-Level
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        currLevel = self.logLevel
        menu = QMenu(self)
        debug = self.LogAction("Debug")
        if currLevel == logging.DEBUG:
            debug.setChecked(True)
        menu.addAction(debug)
        info = self.LogAction("Info")
        if currLevel == logging.INFO:
            info.setChecked(True)
        menu.addAction(info)
        warning = self.LogAction("Warning")
        if currLevel == logging.WARN:
            warning.setChecked(True)
        menu.addAction(warning)
        error = self.LogAction("Error")
        if currLevel == logging.ERROR:
            error.setChecked(True)
        menu.addAction(error)
        crit = self.LogAction("Critical")
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
