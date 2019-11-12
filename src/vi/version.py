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
from threading import Thread
from PyQt5.QtCore import pyqtSignal, QObject
from packaging.version import parse
from vi.cache.cache import Cache

VERSION = "1.2.3"
SNAPSHOT = True  # set to false when releasing
URL = "https://github.com/Subtalime/vintel"
PROGNAME = "Vintel"
DISPLAY = PROGNAME + " " + VERSION + "{dev}".format(dev="-SNAPSHOT" if SNAPSHOT else "")
AUTHOR = "S. Tschache"
AUTHOR_EMAIL = "github@tschache.com"
MAINTAINER = AUTHOR
MAINTAINER_EMAIL = AUTHOR_EMAIL

LOGGER = logging.getLogger(__name__)


def getNewestVersion():
    try:
        newestVersion = Cache().getFromCache("vi_version_available")
        if not newestVersion:
            url = u"http://vintel.tschache.com/resources/current_version.txt"
            newestVersion = requests.get(url).text
            Cache().putIntoCache("vi_version_available", newestVersion)
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
        self.active = True

    def run(self):
        while True:
            if not self.alerted:
                try:
                    # Is there a newer version available?
                    newestVersion = getNewestVersion()
                    if newestVersion and parse(newestVersion) > parse(VERSION):
                        self.newer_version.emit(newestVersion)
                        self.alerted = True
                except Exception as e:
                    LOGGER.error("Failed NotifyNewVersionThread: %s", e)
            if not self.active:
                return

    def quit(self) -> None:
        self.active = False
        LOGGER.debug("Stopping Version-Thread")
