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

import requests
import logging
import queue
import os
from threading import Thread
from PyQt5.QtCore import pyqtSignal, QObject
from packaging.version import parse

VERSION = "1.2.5"
SNAPSHOT = True  # set to false when releasing
URL = "https://github.com/Subtalime/vintel"
PROGNAME = "Vintel"
DISPLAY = PROGNAME + " " + VERSION + "{dev}".format(dev="-SNAPSHOT" if SNAPSHOT else "")
AUTHOR = "S. Tschache"
AUTHOR_EMAIL = "github@tschache.com"
MAINTAINER = AUTHOR
MAINTAINER_EMAIL = AUTHOR_EMAIL

LOGGER = logging.getLogger(__name__)

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def getNewestVersion():
    try:
        url = u"http://vintel.tschache.com/resources/current_version.txt"
        newestVersion = requests.get(url).text
        return newestVersion
    except Exception as e:
        LOGGER.error("Failed version-request: %s", e)
        return "0.0"


class NotifyNewVersionThread(Thread, QObject):
    newer_version = pyqtSignal(str)

    def __init__(self):
        Thread.__init__(self, name="NewVersion")
        QObject.__init__(self)
        LOGGER.debug("Starting Version-Thread")
        self.alerted = False
        self.queue = queue.Queue()
        self.active = True
        self.timeout = 60 * 60 * 6

    # to exit Queue-Timeout
    def addToQueue(self):
        self.queue.put(0)

    def run(self):
        while True:
            if not self.active:
                return
            if not self.alerted:
                # don't spam my server...
                try:
                    # Is there a newer version available?
                    newestVersion = getNewestVersion()
                    if newestVersion and parse(newestVersion) > parse(VERSION):
                        self.newer_version.emit(newestVersion)
                        self.alerted = True
                except Exception as e:
                    LOGGER.error("Failed NotifyNewVersionThread: %s", e)
            try:
                self.queue.get(timeout=self.timeout)
            except:
                pass

    def quit(self) -> None:
        LOGGER.debug("Stopping Version-Thread")
        self.active = False
        self.addToQueue()
