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

import os
from logging.handlers import RotatingFileHandler
import logging
from logging import StreamHandler

from PyQt5 import QtGui, QtWidgets
from vi import version, systemtray, viui
from vi.cache import cache
from vi.resources import resourcePath, getEveChatlogDir, getVintelDir, getVintelLogDir, \
    createResourceDirs
from vi.cache.cache import Cache
from PyQt5.QtWidgets import QApplication, QMessageBox
from vi.esi import EsiInterface
from vi.logger.logconfig import LogConfiguration

LOGGER = logging.getLogger(__name__)

class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        backGroundColor = "#c6d9ec"

        if not sys.platform.startswith("darwin"):
            # this may set the Window-Icon in the Taskbar too
            import ctypes
            myApplicationID = str(
                "{}.{}.{}".format(version.PROGNAME, version.VERSION, version.SNAPSHOT))
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myApplicationID)
            # and maybe this...

        if sys.platform != "win32" and len(sys.argv) <= 2:
            print("Usage: python vintel.py <chatlogsdir>")
            sys.exit(1)

            # Set up paths
        chatLogDirectory = getEveChatlogDir(passedDir=sys.argv[1] if len(sys.argv) > 1 else None)
        if not os.path.exists(chatLogDirectory):
            try:
                os.makedirs(chatLogDirectory)
            except Exception as e:
                print("Error while creating %s" % chatLogDirectory, e)
                raise e
        if not os.path.exists(chatLogDirectory):
            # None of the paths for logs exist, bailing out
            print("no path to logs! %s" % chatLogDirectory)
            QMessageBox.critical(None, "No path to Logs", "No logs found at: " + chatLogDirectory,
                                 QMessageBox.Ok)
            sys.exit(1)

        logLevel = logging.DEBUG
        logging.getLogger().setLevel(logLevel)

        # Setting local directory for cache, resources and logging
        createResourceDirs()

        try:
            splash = QtWidgets.QSplashScreen(QtGui.QPixmap(resourcePath("logo.png")))
        except Exception as e:
            print("Failed to load Splash", e)
            raise e

        cache.Cache.PATH_TO_CACHE = getVintelDir()
        try:
            vintelCache = Cache(forceVersionCheck=True)
        except Exception as e:
            print("Failed to load Cache", e)
            raise e

        logLevel = vintelCache.getFromCache("logging_level")
        if not logLevel:
            logLevel = logging.DEBUG
        logging.getLogger().setLevel(logLevel)
        backColor = vintelCache.getFromCache("background_color")
        if backColor:
            backGroundColor = backColor
        self.setStyleSheet("QWidget { background-color: %s; }" % backGroundColor)

        LogConfiguration(log_folder=getVintelLogDir())

        LOGGER.info("------------------- %s %s starting up -------------------", version.PROGNAME,
                     version.VERSION)
        LOGGER.info("Looking for chat logs at: %s", getEveChatlogDir())
        LOGGER.info("Cache maintained here: %s", cache.Cache.PATH_TO_CACHE)
        LOGGER.info("Writing logs to: %s", getVintelLogDir())
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
import traceback
from vi.version import VERSION, PROGNAME, AUTHOR, AUTHOR_EMAIL

__name__ = PROGNAME
__author__ = AUTHOR + " (" + AUTHOR_EMAIL + ")"
__version__ = VERSION

import ftplib
import time


def __uploadLog():
    """
    upload Log-File for further analysis
    :return: None
    """
    try:
        session = ftplib.FTP("vintel.tschache.com", "vintellog", "jYie93#7")
        logFilename = os.path.join(getVintelLogDir(), "output.log")
        file_hdl = open(logFilename, "rb")
        dest = str(time.time()) + "_output.log"
        session.storlines("STOR " + dest, file_hdl)
        file_hdl.close()
        session.quit()
    except Exception as e:
        LOGGER.error("Problem uploading Log-File", e)
        pass


def myExceptionHook(exceptionType, exceptionValue, tracebackObject):
    """
        Global function to catch unhandled exceptions.
    """
    try:
        LOGGER.critical("-- Unhandled Exception --")
        LOGGER.critical(''.join(traceback.format_tb(tracebackObject)))
        LOGGER.critical('{0}: {1}'.format(exceptionType, exceptionValue))
        LOGGER.critical("-- ------------------- --")
        __uploadLog()
    except Exception:
        pass


sys.excepthook = myExceptionHook

app = Application(sys.argv)
sys.exit(app.exec_())
