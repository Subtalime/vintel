#!/usr/bin/env python
###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
# 																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
# 																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
# 																		  #
# 																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import ftplib
import logging
import os
import sys
import time
import traceback

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox

from vi.systemtray import TrayIcon
from vi.viui import MainWindow
from vi.cache.cache import Cache
from vi.color.helpers import contrast_color, string_to_color
from vi.esi import EsiInterface
from vi.logger.logconfig import LogConfiguration
from vi.resources import (
    createResourceDirs,
    getEveChatlogDir,
    getVintelDir,
    getVintelLogDir,
    resourcePath,
)
from vi.settings.settings import GeneralSettings
from vi.version import AUTHOR, AUTHOR_EMAIL, PROGNAME, VERSION, SNAPSHOT


class MyMainException(Exception):
    pass


class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        self.LOGGER = logging.getLogger(__name__)
        self.backGroundColor = "#ffffff"
        self.splash = None
        self.vintelCache = None
        self.logLevel = None
        self.chatLogDirectory = None
        self.trayIcon = None
        self.mainWindow = None

        if not sys.platform.startswith("darwin"):
            # this may set the Window-Icon in the Taskbar too
            import ctypes

            my_app_id = u"{}.{}.{}".format(PROGNAME, VERSION, SNAPSHOT)
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
            # and maybe this...

        if sys.platform != "win32" and len(sys.argv) <= 2:
            msg = "Usage: python vintel.py <chatlogsdir>"
            raise MyMainException(msg, NotImplementedError)

    def configure(self):
        # Set up paths
        self.chatLogDirectory = getEveChatlogDir(
            passedDir=sys.argv[1] if len(sys.argv) > 1 else None
        )
        if not os.path.exists(self.chatLogDirectory):
            try:
                os.makedirs(self.chatLogDirectory)
            except Exception as e:
                raise MyMainException(
                    "Error while creating %s" % self.chatLogDirectory, e
                )
        if not os.path.exists(self.chatLogDirectory):
            # None of the paths for logs exist, bailing out
            msg = "no path to logs! %s" % self.chatLogDirectory
            QMessageBox.critical(
                None,
                "No path to Logs",
                "No logs found at: " + self.chatLogDirectory,
                QMessageBox.Ok,
            )
            raise MyMainException(msg, PermissionError)

        createResourceDirs(True)
        LogConfiguration()
        try:
            self.splash = QtWidgets.QSplashScreen(
                QtGui.QPixmap(resourcePath("logo.png"))
            )
        except Exception as e:
            raise MyMainException("Failed to load Splash", e)

        Cache.PATH_TO_CACHE = getVintelDir()
        try:
            self.vintelCache = Cache(force_version_check=True)
        except Exception as e:
            raise MyMainException("Failed to load Cache", e)

        self.logLevel = GeneralSettings().log_level
        logging.getLogger().setLevel(self.logLevel)
        # self.backGroundColor = GeneralSettings().background_color
        # foreground = contrast_color(string_to_color(self.backGroundColor))
        # self.setStyleSheet(
        #     "QWidget { background-color: %s; color: %s; }"
        #     % (self.backGroundColor, foreground)
        # )

        logging.getLogger().info(
            "------------------- %s %s starting up -------------------",
            PROGNAME,
            VERSION,
        )
        logging.getLogger().info("Looking for chat logs at: %s", getEveChatlogDir())
        logging.getLogger().info("Cache maintained here: %s", Cache.PATH_TO_CACHE)
        logging.getLogger().info("Writing logs to: %s", getVintelLogDir())
        # let's hope, this will speed up start-up
        EsiInterface(cache_dir=getVintelDir())

    def startup(self):
        self.splash.show()
        self.processEvents()
        self.trayIcon = TrayIcon(self)
        self.trayIcon.show()
        self.mainWindow = MainWindow(
            self.chatLogDirectory, self.trayIcon, self.backGroundColor
        )
        self.mainWindow.show()
        self.mainWindow.raise_()
        self.splash.finish(self.mainWindow)


__name__ = PROGNAME
__author__ = AUTHOR + " (" + AUTHOR_EMAIL + ")"
__version__ = VERSION


# TODO: Get log file from logconfig!
def __uploadLog():
    """
    upload Log-File for further analysis
    :return: None
    """
    try:
        session = ftplib.FTP("vintel.tschache.com", "vintellog", "jYie93#7")
        log_filename = LogConfiguration.LOG_FILE_PATH
        file_hdl = open(log_filename, "rb")
        destination = str(time.time()) + "_output.log"
        session.storlines("STOR " + destination, file_hdl)
        file_hdl.close()
        session.quit()
    except Exception as e:
        logging.getLogger().error("Problem uploading Log-File", e)


def main_exception_hook(exceptionType, exceptionValue, tracebackObject):
    """
        Global function to catch unhandled exceptions.
    """
    logging.getLogger().critical("-- Unhandled Exception --")
    logging.getLogger().critical("".join(traceback.format_tb(tracebackObject)))
    logging.getLogger().critical("{0}: {1}".format(exceptionType, exceptionValue))
    logging.getLogger().critical("-- ------------------- --")
    __uploadLog()


# sys.excepthook = main_exception_hook

app = Application(sys.argv)
app.configure()
app.startup()
result = app.exec_()
# sys.exit(result)
