#!/usr/bin/env python
###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#																		  #
#																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import sys
import os
import logging

from logging.handlers import RotatingFileHandler
from logging import StreamHandler

from PyQt5 import QtGui, QtWidgets
from vi import version
from vi.ui import viui
from vi.ui import systemtray
from vi.cache import cache
from vi.resources import resourcePath, getEveChatlogDir, getVintelDir, getVintelLogDir, createResourceDirs
from vi.cache.cache import Cache
from PyQt5.QtWidgets import QApplication, QMessageBox
from vi.esi import EsiInterface

class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        backGroundColor = "#c6d9ec"

        if not sys.platform.startswith("darwin"):
            # this may set the Window-Icon in the Taskbar too
            import ctypes
            myApplicationID = str("{}.{}.{}".format(version.PROGNAME, version.VERSION, version.SNAPSHOT))
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myApplicationID)

        if sys.platform != "win32" and len(sys.argv) <= 2:
            print("Usage: python vintel.py <chatlogsdir>")
            sys.exit(1)

            # Set up paths
        chatLogDirectory = getEveChatlogDir(passedDir=sys.argv[1] if len(sys.argv) > 1 else None)
        if not os.path.exists(chatLogDirectory):
            os.makedirs(chatLogDirectory)
        if not os.path.exists(chatLogDirectory):
            # None of the paths for logs exist, bailing out
            QMessageBox.critical(None, "No path to Logs", "No logs found at: " + chatLogDirectory, QMessageBox.Ok)
            sys.exit(1)

        # Setting local directory for cache, resources and logging
        createResourceDirs()
        splash = QtWidgets.QSplashScreen(QtGui.QPixmap(resourcePath("vi/ui/res/logo.png")))

        cache.Cache.PATH_TO_CACHE = os.path.join(getVintelDir(), "cache-2.sqlite3")
        vintelCache = Cache()
        logLevel = vintelCache.getFromCache("logging_level")
        if not logLevel:
            logLevel = logging.DEBUG
        logging.getLogger().setLevel(logLevel)
        backColor = vintelCache.getFromCache("background_color")
        if backColor:
            backGroundColor = backColor
        self.setStyleSheet("QWidget { background-color: %s; }" % backGroundColor)

        # Setup logging for console and rotated log files
        formatter = logging.Formatter('%(asctime)s|%(levelname)s %(module)s/%(funcName)s: %(message)s', datefmt='%d/%m %H:%M:%S')
        rootLogger = logging.getLogger()
        # rootLogger.setLevel(level=logLevel)

        logFilename = os.path.join(getVintelLogDir(), "output.log")
        fileHandler = RotatingFileHandler(maxBytes=(1048576*5), backupCount=7, filename=logFilename, mode='a')
        fileHandler.setFormatter(formatter)
        # in the log file, ALWAYS debug
        fileHandler.setLevel(logging.DEBUG)
        rootLogger.addHandler(fileHandler)

        # stdout
        consoleHandler = StreamHandler()
        consoleHandler.setFormatter(formatter)
        consoleHandler.setLevel(logLevel)
        # output logging to a Window
        rootLogger.addHandler(consoleHandler)
        logging.info("------------------- %s %s starting up -------------------", version.PROGNAME, version.VERSION)
        logging.info("Looking for chat logs at: %s", getEveChatlogDir())
        logging.info("Cache maintained here: %s", cache.Cache.PATH_TO_CACHE)
        logging.info("Writing logs to: %s", getVintelLogDir())
        # let's hope, this will speed up start-up
        EsiInterface(cache_dir=getVintelDir())
        splash.show()
        self.processEvents()
        trayIcon = systemtray.TrayIcon(self)
        trayIcon.show()
        self.mainWindow = viui.MainWindow(chatLogDirectory, trayIcon, backGroundColor)
        self.mainWindow.show()
        self.mainWindow.raise_()
        splash.finish(self.mainWindow)

import sys
import logging
import traceback
from vi.version import VERSION, PROGNAME
__name__ = PROGNAME
__author__ = "Steven Tschache (github@tschache.com)"
__version__ = VERSION

logger = logging.getLogger(__name__)

def exceptHook(exceptionType, exceptionValue, tracebackObject):
    """
        Global function to catch unhandled exceptions.
    """
    try:
        logger.critical("-- Unhandled Exception --")
        logger.critical(''.join(traceback.format_tb(tracebackObject)))
        logger.critical('{0}: {1}'.format(exceptionType, exceptionValue))
        logger.critical("-- ------------------- --")
    except Exception:
        pass

sys.excepthook = exceptHook

app = Application(sys.argv)
sys.exit(app.exec_())

