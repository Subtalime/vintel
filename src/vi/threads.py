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

from six.moves import queue as SixQueue
import queue
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, QTimer, pyqtSignal, QPointF

from vi import koschecker
from vi.cache.cache import Cache
from vi.resources import resourcePath
from vi.chatentrywidget import ChatEntryWidget
from vi.esi.EsiHelper import EsiHelper
STATISTICS_UPDATE_INTERVAL_MSECS = 1 * 60 * 1000

# attempt to run this in a thread rather thana timer
# to reduce flickering on reload
class MapUpdateThread(QThread):
    map_update = pyqtSignal(str)

    def __init__(self, timerInterval: int=4000):
        QThread.__init__(self)
        logging.debug("Starting Map-Thread {}".format(timerInterval))
        self.queue = queue.Queue()
        self.activeData = False
        self.timeout = timerInterval / 1000

    def run(self):
        def injectScrollPosition(content: str, scroll: str) -> str:
            soup = BeautifulSoup(content, "html.parser")
            js = soup.new_tag("script", attrs={"type": "text/javascript"})
            js.string = scroll
            soup.svg.append(js)
            return str(soup)
            # newContent = content
            # if scroll:
            #     scrollText = """\n<script type="text/javascript"><![CDATA[""" + scroll + """]]></script>\n"""
            #     newContent = newContent.replace("</svg>", scrollText + "</svg>")
            # return newContent

        while True:
            try:
                timeout = False
                content, zoomFactor, scrollPosition = self.queue.get(timeout=self.timeout)
            except Exception:
                timeout  = True
                pass
            if not self.activeData: # we don't have initial Map-Data yet
                logging.debug("Map-Content update attempt, but not active")
                continue
            try:
                if not timeout:  # not based on Timeout
                    logging.debug("Setting Map-Content start")
                    zoomfactor = float(zoomFactor)
                    scrollTo = ""
                    if scrollPosition:
                        logging.debug("Current Scroll-Position {}".format(scrollPosition))
                        scrollTo = str("window.scrollTo({:.0f}, {:.0f});".
                                       format(scrollPosition.x() / zoomfactor,
                                              scrollPosition.y() / zoomfactor))
                    newContent = injectScrollPosition(content, scrollTo)
                    self.map_update.emit(newContent)
                    logging.debug("Setting Map-Content complete")
                else:
                    logging.debug("Map-Content from Cache")
                    self.map_update.emit(None)
            except Exception as e:
                logging.error("Problem with setMapContent: %r", e)

    def quit(self):
        self.active = False
        logging.debug("Stopping Map-Thread")
        self.queue.put(None)
        QThread.quit(self)


class AvatarFindThread(QThread):
    avatar_update = pyqtSignal(ChatEntryWidget, bytes)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting Avatar-Thread")
        self.queue = SixQueue.Queue()
        self.active = True


    def addChatEntry(self, chatEntry, clearCache=False):
        try:
            if clearCache:
                cache = Cache()
                cache.removeAvatar(chatEntry.message.user)

            # Enqeue the data to be picked up in run()
            self.queue.put(chatEntry)
        except Exception as e:
            logging.error("Error in AvatarFindThread: %s", e)


    def run(self):
        cache = Cache()
        lastCall = 0
        wait = 300  # time between 2 requests in ms
        while True:
            try:
                # Block waiting for addChatEntry() to enqueue something
                chatEntry = self.queue.get()
                if not self.active:
                    continue
                charname = chatEntry.message.user
                logging.debug("AvatarFindThread getting avatar for %s" % charname)
                avatar = None
                if charname == "VINTEL":
                    with open(resourcePath("vi/ui/res/logo_small.png"), "rb") as f:
                        avatar = f.read()
                if not avatar:
                    avatar = cache.getAvatar(charname)
                    if avatar:
                        logging.debug("AvatarFindThread found cached avatar for %s" % charname)
                if not avatar:
                    diffLastCall = time.time() - lastCall
                    if diffLastCall < wait:
                        time.sleep((wait - diffLastCall) / 1000.0)
                    avatar = EsiHelper().getAvatarByName(charname)
                    # avatar = evegate.EveGate().getAvatarForPlayer(charname)
                    lastCall = time.time()
                    if avatar:
                        cache.putAvatar(charname, avatar)
                if avatar:
                    logging.debug("AvatarFindThread emit avatar_update for %s" % charname)
                    self.avatar_update.emit(chatEntry, avatar)
            except Exception as e:
                logging.error("Error in AvatarFindThread : %s", e)


    def quit(self):
        self.active = False
        logging.debug("Stopping Avatar-Thread")
        self.queue.put(None)
        QThread.quit(self)


class KOSCheckerThread(QThread):
    kos_result = pyqtSignal(str, int, bool)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting KOSChecker-Thread")
        self.queue = SixQueue.Queue()
        self.recentRequestNamesAndTimes = {}
        self.active = True


    def addRequest(self, names, requestType, onlyKos=False):
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
            logging.error("Error in KOSCheckerThread.addRequest: %s", e)


    def run(self):
        while True:
            # Block waiting for addRequest() to enqueue something
            names, requestType, onlyKos = self.queue.get()
            if not self.active:
                return
            try:
                #logging.info("KOSCheckerThread kos checking %s" %  str(names))
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
                logging.error("Error in KOSCheckerThread.run: %s", e)
                continue

            logging.info("KOSCheckerThread emitting kos_result for: state = {0}, text = {1}, requestType = {2}, hasKos = {3}".format(
                    "ok", text, requestType, hasKos))
            self.kos_result.emit(text, requestType, hasKos)
            # self.emit(PYQT_SIGNAL("kos_result"), "ok", text, requestType, hasKos)

    def quit(self):
        self.active = False
        logging.debug("Stopping KOSChecker-Thread")
        self.queue.put((None, None, None))
        QThread.quit(self)


class MapStatisticsThread(QThread):
    statistic_data_update = pyqtSignal(dict)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting MapStatistics-Thread")
        self.queue = SixQueue.Queue(maxsize=1)
        self.lastStatisticsUpdate = time.time()
        self.pollRate = STATISTICS_UPDATE_INTERVAL_MSECS
        self.refreshTimer = None
        self.active = True


    def requestStatistics(self):
        self.queue.put(1)


    def run(self):
        self.refreshTimer = QTimer()
        # self.connect(self.refreshTimer, PYQT_SIGNAL("timeout()"), self.requestStatistics)
        self.refreshTimer.timeout.connect(self.requestStatistics)
        while True:
            # Block waiting for requestStatistics() to enqueue a token
            self.queue.get()
            if not self.active:
                return
            self.refreshTimer.stop()
            logging.debug("MapStatisticsThread requesting statistics")
            try:
                statistics = EsiHelper().getSystemStatistics()
                # statistics = evegate.EveGate().getSystemStatistics()
                #time.sleep(2)  # sleeping to prevent a "need 2 arguments"-error
                requestData = {"result": "ok", "statistics": statistics}
            except Exception as e:
                logging.error("Error in MapStatisticsThread: %s", e)
                requestData = {"result": "error", "text": six.text_type(e)}
            self.lastStatisticsUpdate = time.time()
            self.refreshTimer.start(self.pollRate)
            self.statistic_data_update.emit(requestData)
            # self.emit(PYQT_SIGNAL("statistic_data_update"), requestData)
            logging.debug("MapStatisticsThread emitted statistic_data_update")


    def quit(self):
        self.active = False
        logging.debug("Stopping MapStatistics-Thread")
        self.queue.put(None)
        QThread.quit(self)
