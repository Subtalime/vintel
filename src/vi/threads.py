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

import time
import logging
import six
import os
import stat
import glob

from six.moves import queue as SixQueue
import queue
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, QTimer, pyqtSignal

from vi import koschecker
from vi.cache.cache import Cache
from vi.resources import resourcePath, getVintelDir
from vi.chat.chatentrywidget import ChatEntryWidget
from vi.esi.esihelper import EsiHelper

STATISTICS_UPDATE_INTERVAL_MSECS = (1 * 60) * 1000  # every hour
FILE_DEFAULT_MAX_AGE = 60 * 60 * 4  # oldest Chatlog-File to scan (4 hours)

LOGGER = logging.getLogger(__name__)


# attempt to run this in a thread rather than a timer
# to reduce flickering on reload
class MapUpdateThread(QThread):
    map_update = pyqtSignal(str)

    def __init__(self, timerInterval: int = 4000):
        QThread.__init__(self)
        logging.debug("Starting Map-Thread {}".format(timerInterval))
        self.queue = queue.Queue()
        self._active = False
        self.paused = False
        if timerInterval > 1000:
            timerInterval = timerInterval / 1000
        self.timeout = timerInterval

    def addToQueue(self, content=None, zoomfactor=None, scrollposition=None):
        self.queue.put((content, zoomfactor, scrollposition))

    def start(self, priority: 'QThread.Priority' = QThread.NormalPriority) -> None:
        logging.debug("Starting MapUpdate Thread")
        self._active = True
        super(MapUpdateThread, self).start(priority)

    def pause(self, pause_update: bool) -> None:
        self.paused = pause_update

    def run(self):
        def injectScrollPosition(svg_content: str, scroll: str) -> str:
            soup = BeautifulSoup(svg_content, "html.parser")
            js = soup.new_tag("script", attrs={"type": "text/javascript"})
            js.string = scroll
            soup.svg.append(js)
            return str(soup)

        load_map_attempt = 0
        while self._active:
            try:
                timeout = False
                content, zoom_factor, scroll_position = self.queue.get(timeout=self.timeout)
            except Exception:
                timeout = True
                pass
            if timeout and self.paused:  # we don't have initial Map-Data yet
                load_map_attempt += 1
                logging.debug("Map-Content update attempt, but not active")
                if load_map_attempt > 10:
                    logging.critical("Something is stopping the program of progressing. (Map-Attempts > 10\n"
                                     "If this continues to happen, delete the Cache-File in \"%s\"" % getVintelDir())
                    self.quit()
                    return
                continue
            elif self.paused and not content:
                logging.debug("No Map-Content received. Ending MapUpdate Thread")
                self.quit()
                return
            try:
                load_map_attempt = 0
                if not timeout and content:  # not based on Timeout
                    logging.debug("Setting Map-Content start")
                    zoom_factor = zoom_factor if zoom_factor else 1.
                    # zoom_factor = float(zoom_factor)
                    scroll_to = ""
                    if scroll_position:
                        logging.debug("Current Scroll-Position {}".format(scroll_position))
                        scroll_to = str("window.scrollTo({:.0f}, {:.0f});".
                                        format(scroll_position.x() / zoom_factor,
                                               scroll_position.y() / zoom_factor))
                    new_content = injectScrollPosition(content, scroll_to)
                    self.map_update.emit(new_content)
                    logging.debug("Setting Map-Content complete")
            except Exception as e:
                logging.error("Problem with setMapContent: %r", e)

    def quit(self):
        if self._active:
            logging.debug("Stopping Map-Thread")
            self._active = False
            self.pause(False)
            self.addToQueue()
            super(MapUpdateThread, self).quit()


class AvatarFindThread(QThread):
    avatar_update = pyqtSignal(ChatEntryWidget, bytes)

    def __init__(self):
        QThread.__init__(self)
        self.queue = SixQueue.Queue()
        self._active = False

    def addChatEntry(self, chatEntry=None, clearCache=False):
        try:
            if clearCache:
                cache = Cache()
                cache.removeAvatar(chatEntry.message.user)

            # Enqeue the data to be picked up in run()
            self.queue.put(chatEntry)
        except Exception as e:
            logging.error("Error in AvatarFindThread: %r", e)

    def start(self, priority: 'QThread.Priority' = QThread.NormalPriority) -> None:
        logging.debug("Starting Avatar-Thread")
        self._active = True
        super(AvatarFindThread, self).start(priority)

    def run(self):
        while self._active:
            try:
                # Block waiting for addChatEntry() to enqueue something
                chat_entry = self.queue.get()
                if not self._active:
                    # logging.debug("Request for Avatar but Thread not enabled")
                    return

                charname = chat_entry.message.user
                logging.debug("AvatarFindThread getting avatar for %s" % charname)
                avatar = None
                if charname == "VINTEL":
                    with open(resourcePath("logo_small.png"), "rb") as f:
                        avatar = f.read()
                if not avatar:
                    avatar = EsiHelper().getAvatarByName(charname)
                if avatar:
                    logging.debug("AvatarFindThread emit avatar_update for %s" % charname)
                    self.avatar_update.emit(chat_entry, avatar)
                else:
                    logging.debug("AvatarFindThread Avator not found for %s" % charname)
            except Exception as e:
                logging.error("Error in AvatarFindThread : %r", e)

    def quit(self):
        if self._active:
            logging.debug("Stopping Avatar-Thread")
            self._active = False
            self.addChatEntry()
            super(AvatarFindThread, self).quit()


class KOSCheckerThread(QThread):
    kos_result = pyqtSignal(str, int, bool)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting KOSChecker-Thread")
        self.queue = SixQueue.Queue()
        self.recentRequestNamesAndTimes = {}
        self._active = False

    def addRequest(self, names=None, requestType=None, onlyKos=False):
        try:
            # Spam control for multi-client users
            now = time.time()
            if names in self.recentRequestNamesAndTimes:
                lastRequestTime = self.recentRequestNamesAndTimes[names]
                if now - lastRequestTime < 10:
                    return
            self.recentRequestNamesAndTimes[names] = now

            # Enqeue the data to be picked up in run()
            self.queue.put((names, requestType, onlyKos))
        except Exception as e:
            logging.error("Error in KOSCheckerThread.addRequest: %r", e)

    def start(self, priority: 'QThread.Priority' = QThread.NormalPriority) -> None:
        logging.debug("Starting KOSChecker-Thread")
        self._active = True
        super(KOSCheckerThread, self).start(priority)

    def run(self):
        while self._active:
            # Block waiting for addRequest() to enqueue something
            names, requestType, onlyKos = self.queue.get()
            if not self.active:
                return
            try:
                # logging.info("KOSCheckerThread kos checking %s" %  str(names))
                hasKos = False
                if not names:
                    continue
                checkResult = koschecker.check(names)
                if not checkResult:
                    continue
                text = koschecker.resultToText(checkResult, onlyKos)
                for name, data in checkResult.items():
                    if data["kos"] in (koschecker.KOS, koschecker.RED_BY_LAST):
                        hasKos = True
                        break
            except Exception as e:
                logging.error("Error in KOSCheckerThread.run: %r", e)
                continue

            logging.info(
                "KOSCheckerThread emitting kos_result for: state = {0}, text = {1}, requestType = {2}, hasKos = {3}".format(
                    "ok", text, requestType, hasKos))
            self.kos_result.emit(text, requestType, hasKos)
            # self.emit(PYQT_SIGNAL("kos_result"), "ok", text, requestType, hasKos)

    def quit(self):
        if self._active:
            logging.debug("Stopping KOSChecker-Thread")
            self._active = False
            self.addRequest()
            super(KOSCheckerThread, self).quit()


class MapStatisticsThread(QThread):
    statistic_data_update = pyqtSignal(dict)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting MapStatistics-Thread")
        self.queue = SixQueue.Queue(maxsize=1)
        self.lastStatisticsUpdate = time.time()
        self.pollRate = STATISTICS_UPDATE_INTERVAL_MSECS
        self.refreshTimer = None
        self._active = False

    def requestStatistics(self):
        self.queue.put(1)

    def start(self, priority: 'QThread.Priority' = QThread.NormalPriority) -> None:
        logging.debug("Starting Map-Statistic-Update-Thread")
        self._active = True
        super(MapStatisticsThread, self).start(priority)

    def run(self):
        self.refreshTimer = QTimer()
        self.refreshTimer.timeout.connect(self.requestStatistics)
        while self._active:
            # Block waiting for requestStatistics() to enqueue a token
            self.queue.get()
            if not self._active:
                return
            self.refreshTimer.stop()
            logging.debug("MapStatisticsThread requesting statistics")
            try:
                statistics = EsiHelper().getSystemStatistics()
                # statistics = evegate.EveGate().getSystemStatistics()
                # time.sleep(2)  # sleeping to prevent a "need 2 arguments"-error
                requestData = {"result": "ok", "statistics": statistics}
            except Exception as e:
                logging.error("Error in MapStatisticsThread: %r", e)
                requestData = {"result": "error", "text": six.text_type(e)}
            self.lastStatisticsUpdate = time.time()
            self.refreshTimer.start(self.pollRate)
            self.statistic_data_update.emit(requestData)
            logging.debug("MapStatisticsThread emitted statistic_data_update")

    def quit(self):
        if self._active:
            logging.debug("Stopping MapStatistics-Thread")
            self._active = False
            self.requestStatistics()
            super(MapStatisticsThread, self).quit()


class ChatTidyThread(QThread):
    time_up = pyqtSignal()

    def __init__(self, max_age: int = 20 * 60, interval: float = 60):
        QThread.__init__(self)
        logging.debug("Starting ChatTidy-Thread")
        self._active = False
        self.interval = interval
        self.max_age = max_age
        self.queue = SixQueue.Queue(maxsize=1)

    def start(self, priority: 'QThread.Priority' = QThread.NormalPriority) -> None:
        logging.debug("Starting Chat-Tidy-Up-Thread")
        self._active = True
        super(ChatTidyThread, self).start(priority)

    def run(self):
        while self._active:
            try:
                self.queue.get(timeout=self.interval)
            except Exception:
                pass
            if self._active:
                self.time_up.emit()

    def quit(self):
        if self._active:
            logging.debug("Stopping ChatTidy-Thread")
            self._active = False
            self.queue.put(1)
            super(ChatTidyThread, self).quit()


