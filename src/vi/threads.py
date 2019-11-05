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
from vi.resources import resourcePath
from vi.chatentrywidget import ChatEntryWidget
from vi.esihelper import EsiHelper


STATISTICS_UPDATE_INTERVAL_MSECS = 1 * 60 * 1000
FILE_DEFAULT_MAX_AGE = 60 * 60 * 24


# attempt to run this in a thread rather thana timer
# to reduce flickering on reload
class MapUpdateThread(QThread):
    map_update = pyqtSignal(str)

    def __init__(self, timerInterval: int=4000):
        QThread.__init__(self)
        logging.debug("Starting Map-Thread {}".format(timerInterval))
        self.queue = queue.Queue()
        self.activeData = False
        if timerInterval > 1000:
            timerInterval = timerInterval / 1000
        self.timeout = timerInterval

    def run(self):
        def injectScrollPosition(svg_content: str, scroll: str) -> str:
            soup = BeautifulSoup(svg_content, "html.parser")
            js = soup.new_tag("script", attrs={"type": "text/javascript"})
            js.string = scroll
            soup.svg.append(js)
            return str(soup)

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
                    zoomfactor = zoomFactor if zoomFactor else 1.
                    # zoomfactor = float(zoomFactor)
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
                    pass
                    # logging.debug("Map-Content from Cache")
                    # self.map_update.emit(None)
            except Exception as e:
                logging.error("Problem with setMapContent: %r", e)

    def quit(self):
        self.activeData = False
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
            logging.error("Error in AvatarFindThread: %r", e)


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
                    lastCall = time.time()
                    if avatar:
                        cache.putAvatar(charname, avatar)
                if avatar:
                    logging.debug("AvatarFindThread emit avatar_update for %s" % charname)
                    self.avatar_update.emit(chatEntry, avatar)
            except Exception as e:
                logging.error("Error in AvatarFindThread : %r", e)


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
            logging.error("Error in KOSCheckerThread.addRequest: %r", e)


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
                logging.error("Error in KOSCheckerThread.run: %r", e)
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
                logging.error("Error in MapStatisticsThread: %r", e)
                requestData = {"result": "error", "text": six.text_type(e)}
            self.lastStatisticsUpdate = time.time()
            self.refreshTimer.start(self.pollRate)
            self.statistic_data_update.emit(requestData)
            logging.debug("MapStatisticsThread emitted statistic_data_update")


    def quit(self):
        self.active = False
        logging.debug("Stopping MapStatistics-Thread")
        self.queue.put(None)
        QThread.quit(self)

class FileWatcherThread(QThread):
    file_change = pyqtSignal(str)

    def __init__(self, folder, maxAge=FILE_DEFAULT_MAX_AGE):
        super(__class__, self).__init__()
        logging.debug("Starting FileWatcher-Thread")
        self.folder = folder
        self.active = True
        self._warned = False
        self.maxAge = maxAge
        self.maxFiles = 200
        # index = Folder, content = {path, os.stat}
        self.filesInFolder = {}
        self._addFiles(folder)

    def addPath(self, path):
        self._addFiles(path)

    def run(self):
        while True:
            # don't overload the disk scanning
            time.sleep(0.5)
            # here, periodically, we check if any files have been added to the folder
            if self.active:
                self._scanPaths()
                for path in self.filesInFolder.keys(): # dict
                    self.filesInFolder[path] = self._checkChanges(list(self.filesInFolder[path].items()))
            pass

    def quit(self) -> None:
        self.active = False
        logging.debug("Stopping FileWatcher-Thread")
        super(__class__, self).quit()

    def fileChanged(self, path):
        self.file_change.emit(path)

    def _sendWarning(self, path, length):
        # only do this ONCE at startup
        if self._warned:
            return
        logging.warning("Log-Folder \"{}\" has more than {} files (actually has {})! This will impact performance! Consider tidying up!".format(path, self.maxFiles, length))
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
        folderContent = sorted(glob.glob(os.path.join(path, "*")), key=os.path.getmtime, reverse=True)
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
                    filesInDir.pop(fullPath)
                    changed = True
            except Exception:
                pass
        if changed:
            self.filesInFolder[path] = filesInDir

