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
from PyQt5.QtCore import QTimer, QObject
from threading import Thread
import time
import queue
import logging
from .esiinterface import EsiInterface


LOGGER = logging.getLogger(__name__)
# This is purely to load ESI in the background, since it can take quite a while!
# Once loaded, the thread can actually be stopped
class EsiThread(Thread, QObject):
    POLL_RATE = 5000

    def __init__(self, use_cache: bool = True, cache_directory: str = None):
        Thread.__init__(self, name="Esi")
        QObject.__init__(self)
        LOGGER.debug("Starting ESI Thread")
        self.__use_cache = use_cache
        # if use_cache and cache_directory and not os.path.exists(cache_directory):
        #     raise AttributeError("\"cache_directory\" (%s) does not exist!" % cache_directory)
        self.__cache_dir = cache_directory
        self.queue = queue.Queue(maxsize=1)
        self.lastStatisticsUpdate = time.time()
        self.pollRate = self.POLL_RATE
        self.refreshTimer = None
        self.__esiComplete = False
        self.active = True
        # self.requestInstance()

    def requestInstance(self):
        self.queue.put(1)

    def hasEsi(self):
        return self.__esiComplete

    def run(self):
        self.refreshTimer = QTimer()
        self.refreshTimer.timeout.connect(self.requestInstance)
        while True:
            # Block waiting for requestStatistics() to enqueue a token
            req = self.queue.get(False)
            if not self.active:
                return
            if req != 1:
                continue
            # this should stop any kind of future polling
            self.refreshTimer.stop()
            # this can take a while... loading Swagger and loading Ship-Data
            try:
                # load the Interface
                EsiInterface(use_caching=self.__use_cache, cache_dir=self.__cache_dir)
                self.__esiComplete = True
                # used frequently, so pre-load
                EsiInterface().getShipList
            except Exception as e:
                raise e
            self.lastStatisticsUpdate = time.time()
            self.refreshTimer.start(self.pollRate)

    def quit(self):
        self.active = False
        LOGGER.debug("Stopping ESI Thread")
