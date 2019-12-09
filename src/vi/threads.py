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
FILE_DEFAULT_MAX_AGE = 60 * 60 * 24  # oldest Chatlog-File to scan

LOGGER = logging.getLogger(__name__)


# attempt to run this in a thread rather thana timer
# to reduce flickering on reload
class MapUpdateThread(QThread):
    map_update = pyqtSignal(str)

    def __init__(self, timerInterval: int = 4000):
        QThread.__init__(self)
        logging.debug("Starting Map-Thread {}".format(timerInterval))
        self.queue = queue.Queue()
        self.active = False
        if timerInterval > 1000:
            timerInterval = timerInterval / 1000
        self.timeout = timerInterval

    def addToQueue(self, content=None, zoomfactor=None, scrollposition=None):
        self.queue.put((content, zoomfactor, scrollposition))

    def run(self):
        def injectScrollPosition(svg_content: str, scroll: str) -> str:
            soup = BeautifulSoup(svg_content, "html.parser")
            js = soup.new_tag("script", attrs={"type": "text/javascript"})
            js.string = scroll
            soup.svg.append(js)
            return str(soup)

        load_map_attempt = 0
        while True:
            try:
                timeout = False
                content, zoom_factor, scroll_position = self.queue.get(timeout=self.timeout)
            except Exception:
                timeout = True
                pass
            if timeout and not self.active:  # we don't have initial Map-Data yet
                load_map_attempt += 1
                logging.debug("Map-Content update attempt, but not active")
                if load_map_attempt > 10:
                    logging.critical("Something is stopping the program of progressing. (Map-Attempts > 10\n"
                                     "If this continues to happen, delete the Cache-File in \"%s\"" % getVintelDir())
                    return
                continue
            elif not self.active and not content:
                logging.debug("Ending MapUpdate Thread")
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
        logging.debug("Stopping Map-Thread")
        self.active = False
        self.addToQueue()
        QThread.quit(self)


class AvatarFindThread(QThread):
    avatar_update = pyqtSignal(ChatEntryWidget, bytes)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting Avatar-Thread")
        self.queue = SixQueue.Queue()
        self.active = True

    def addChatEntry(self, chatEntry=None, clearCache=False):
        try:
            if clearCache:
                cache = Cache()
                cache.removeAvatar(chatEntry.message.user)

            # Enqeue the data to be picked up in run()
            self.queue.put(chatEntry)
        except Exception as e:
            logging.error("Error in AvatarFindThread: %r", e)

    def run(self):
        while True:
            try:
                # Block waiting for addChatEntry() to enqueue something
                chat_entry = self.queue.get()
                if not self.active:
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
        logging.debug("Stopping Avatar-Thread")
        self.active = False
        self.addChatEntry()
        QThread.quit(self)


class KOSCheckerThread(QThread):
    kos_result = pyqtSignal(str, int, bool)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting KOSChecker-Thread")
        self.queue = SixQueue.Queue()
        self.recentRequestNamesAndTimes = {}
        self.active = True

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

    def run(self):
        while True:
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
        logging.debug("Stopping KOSChecker-Thread")
        self.active = False
        self.addRequest()
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
        logging.debug("Stopping MapStatistics-Thread")
        self.active = False
        self.requestStatistics()
        QThread.quit(self)


class ChatTidyThread(QThread):
    time_up = pyqtSignal()

    def __init__(self, max_age: int = 20 * 60, interval: float = 60):
        QThread.__init__(self)
        logging.debug("Starting ChatTidy-Thread")
        self.active = True
        self.interval = interval
        self.max_age = max_age
        self.queue = SixQueue.Queue(maxsize=1)

    def run(self):
        while self.active:
            try:
                self.queue.get(timeout=self.interval)
            except Exception:
                pass
            if self.active:
                self.time_up.emit()

    def quit(self):
        logging.debug("Stopping ChatTidy-Thread")
        self.active = False
        self.queue.put(1)
        QThread.quit(self)


class FileWatcherThread(QThread):
    file_change = pyqtSignal(str)

    def __init__(self, folder, maxAge=FILE_DEFAULT_MAX_AGE, scan_interval: float = 0.5):
        super(__class__, self).__init__()
        logging.debug("Starting FileWatcher-Thread")
        self.folder = folder
        self.active = True
        self._warned = False
        self.maxAge = maxAge
        self.scanInterval = scan_interval
        self.maxFiles = 200
        # index = Folder, content = {path, os.stat}
        self.filesInFolder = {}
        self._addFiles(folder)

    def addPath(self, path):
        self._addFiles(path)

    def run(self):
        while True:
            # don't overload the disk scanning
            time.sleep(self.scanInterval)
            # here, periodically, we check if any files have been added to the folder
            if self.active:
                self._scanPaths()
                for path in self.filesInFolder.keys():  # dict
                    self.filesInFolder[path] = self._checkChanges(list(self.filesInFolder[path].items()))
            else:
                return

    def quit(self) -> None:
        self.active = False
        logging.debug("Stopping FileWatcher-Thread")
        QThread.quit(self)

    def fileChanged(self, path):
        self.file_change.emit(path)

    def _sendWarning(self, path, length):
        # only do this ONCE at startup
        if self._warned:
            return
        logging.warning(
            "Log-Folder \"{}\" has more than {} files (actually has {})! This will impact performance! Consider tidying up!".format(
                path, self.maxFiles, length))
        self._warned = True

    def _checkChanges(self, checkList):
        fileList = {}

        for file, fstat in checkList:
            # might be tidying up..., so try
            try:
                pathStat = os.stat(file)
                if pathStat != fstat:
                    fstat = pathStat
                    self.fileChanged(file)
                fileList[file] = fstat
            except Exception as e:
                logging.warning("Filewatcher-Thread error on \"%s\": %r", file, e)
                pass
        return fileList

    # scan all configured paths
    def _scanPaths(self):
        for path in self.filesInFolder.keys():
            self._addFiles(path)

    # check for new files in folder and add if necessary
    def _addFiles(self, path):
        filesInDir = self.filesInFolder[path] if path in self.filesInFolder.keys() else {}
        changed = False
        now = time.time()
        # order by date descending
        try:
            folderContent = sorted(glob.glob(os.path.join(path, "*")), key=os.path.getmtime, reverse=True)
        except:
            # might be tidying up in the background
            folderContent = ()
        if self.maxFiles and len(folderContent) > self.maxFiles:
            self._sendWarning(path, len(folderContent))
        for fullPath in folderContent:
            try:
                pathStat = os.stat(fullPath)
                # this file currently not logged
                if not fullPath in filesInDir:
                    if not stat.S_ISREG(pathStat.st_mode):
                        continue
                    if self.maxAge and ((now - pathStat.st_mtime) > self.maxAge):
                        # we now BREAK, since not interested in older files
                        break
                    filesInDir[fullPath] = pathStat
                    changed = True
                # this file now older than wanted
                elif self.maxAge and (now - pathStat.st_mtime) > self.maxAge:
                    LOGGER.debug("removing old File from tracking (older than %d seconds): %s", self.maxAge, fullPath)
                    filesInDir.pop(fullPath)
                    changed = True
            except Exception:
                pass
        if changed:
            self.filesInFolder[path] = filesInDir
            LOGGER.debug("currently tracking %d files in %s" % (len(filesInDir), path))
            LOGGER.debug("  %r" % self.filesInFolder[path])
