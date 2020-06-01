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
from PyQt5.QtCore import QEvent, Qt
from vi.cache.cache import Cache
import logging
import os
from logging import LogRecord, Formatter
from logging.handlers import QueueHandler
from vi.logger import LogLevelPopup
import vi.version

LOG_WINDOW_HANDLER_NAME = "_LogWindowHandler"


class LogDisplayHandler(QtWidgets.QTextEdit):
    def __init__(self, parent):
        QtWidgets.QTextEdit.__init__(self, parent=parent)
        self.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse or QtCore.Qt.TextBrowserInteraction
        )


class LogTextFieldHandler(logging.Handler, QtCore.QObject):
    appendLogMessage = QtCore.pyqtSignal(str)

    def __init__(
        self,
        parent,
        log_level: int = logging.WARNING,
        log_formatter: Formatter = logging.Formatter(
            "%(asctime)s|%(name)s|%(levelname)s: %(message)s", datefmt="%H:%M:%S"
        ),
    ):
        """Text-Widget to handle output of Log-Message

        :param parent: Parent window
        :param log_level: default Log-Level
        :type log_level: int
        :param log_formatter: logging.Formatter to be used
        :type log_formatter: Formatter
        """
        logging.Handler.__init__(self)
        QtCore.QObject.__init__(self)

        self.setFormatter(log_formatter)
        self.setLevel(log_level)
        self.log_record_text = LogDisplayHandler(parent)
        self.appendLogMessage.connect(self.log_record_text.append)

    def emit(self, record: LogRecord) -> None:
        msg = self.format(record)
        if record.levelno == self.level:
            self.appendLogMessage.emit(msg)


class LogWindow(QtWidgets.QWidget, logging.Handler):
    log_handler = None
    log_level = logging.WARNING
    cache_visible = "log_window_visible"
    cache_size = "log_window"
    cache_level = "log_window_level"
    icon_path = None

    def __init__(self, parent=None, log_handler: QueueHandler = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.LOGGER = logging.getLogger(__name__)
        self.cache = Cache()
        try:
            self.restoreGeometry(self.cache.fetch(self.cache_size))
        except Exception as e:
            self.setBaseSize(400, 600)
            pass
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)
        self.create_content()
        vis = self.cache.fetch(self.cache_visible, default=False)
        if bool(vis):
            self.show()

    def create_content(self):
        self.log_level = self.cache.fetch(self.cache_level, default=self.log_level)
        self.log_handler = LogTextFieldHandler(self, self.log_level)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.get_handler().log_record_text)
        self.setLayout(vbox)
        self.set_handler()
        self.set_title_and_icon()

    def set_handler(self):
        self.get_handler().setLevel(self.log_level)
        formatter = logging.Formatter(
            "%(asctime)s|%(name)s|%(levelname)s: %(message)s", datefmt="%H:%M:%S"
        )
        self.get_handler().setFormatter(formatter)
        # maybe this should be only the Root Logger?
        logging.getLogger().addHandler(self.get_handler())
        # self.LOGGER.addHandler(self.get_handler())

    def get_handler(self):
        return self.log_handler

    def set_title_and_icon(self):
        self.setWindowTitle(
            "{} Logging ({})".format(
                vi.version.DISPLAY, logging.getLevelName(self.log_level)
            )
        )
        if not self.icon_path:
            self.icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "..", "icon.ico"
            )
            if os.path.exists(self.icon_path):
                self.setWindowIcon(QtGui.QIcon(self.icon_path))

    # def changeEvent(self, event: QtCore.QEvent) -> None:
    #     super(LogWindow, self).changeEvent(event)
    #     if event.type() == QEvent.WindowStateChange:
    #         if int(self.windowState()) & Qt.WindowMinimized:
    #             self.cache.put(self.cache_size, self.saveGeometry())
    #             self.cache.put(self.cache_visible, str(False))
    #             self.LOGGER.debug("LogWindow changeEvent hidden")
    #             self.hide()
    #             event.accept()
    #         else:
    #             self.cache.put(self.cache_visible, str(True))
    #             self.LOGGER.debug("LogWindow changeEvent visible")
    #             self.show()
    #             event.accept()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        super(LogWindow, self).closeEvent(event)
        self.cache.put(self.cache_visible, self.isVisible())
        self.cache.put(self.cache_size, self.saveGeometry())
        self.LOGGER.debug("LogWindow closeEvent")
        event.accept()

    # popup to set Log-Level
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        context_menu = LogLevelPopup(self, self.log_level)
        setting = context_menu.exec_(self.mapToGlobal(event.pos()))
        if setting:
            self.LOGGER.debug(
                "Log-Level changed to %d (%s)"
                % (setting.log_level(), logging.getLevelName(setting.log_level()))
            )
            self.log_level = setting.log_level()
            Cache().put(self.cache_level, self.log_level)
            self.get_handler().setLevel(self.log_level)
            self.set_title_and_icon()
