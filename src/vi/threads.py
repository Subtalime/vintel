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
from threading import Thread, local
from six.moves import queue as SixQueue
import queue
from bs4 import BeautifulSoup
from PyQt5.QtCore import QTimer, pyqtSignal, QObject

from vi import koschecker
from vi.cache.cache import Cache
from vi.resources import resourcePath, getVintelDir
from vi.chatentrywidget import ChatEntryWidget
from vi.esihelper import EsiHelper

STATISTICS_UPDATE_INTERVAL_MSECS = 1 * 60 * 1000
FILE_DEFAULT_MAX_AGE = 60 * 60 * 24

LOGGER = logging.getLogger(__name__)


# attempt to run this in a thread rather than a timer
# to reduce flickering on reload
class MapUpdateThread(Thread, QObject):
    map_update = pyqtSignal(str)

    def __init__(self, timerInterval: int = 4000):
        Thread.__init__(self, name="MapUpdate")
        QObject.__init__(self)
        LOGGER.debug("Starting Map-Thread (Interval {}ms)".format(timerInterval))
        self.queue = queue.Queue()
        self.active = True
        self.activeData = False
        if timerInterval > 1000:
            timerInterval = timerInterval / 1000
        self.timeout = timerInterval
        self.maxLoadMapAttempts = 10

    def run(self):
        def injectScrollPosition(svg_content: str, scroll: str) -> str:
            tobj = local()
            tobj.soup = BeautifulSoup(svg_content, "html.parser")
            tobj.js = tobj.soup.new_tag("script", attrs={"type": "text/javascript"})
            tobj.js.string = scroll
            tobj.soup.svg.append(tobj.js)
            return str(tobj.soup)

        loadMapAttempt = 0
        while True:
            tobj = local()
            try:
                tobj.timeout = False
                tobj.content, tobj.zoomFactor, tobj.scrollPosition = self.queue.get(
                    timeout=self.timeout)
            except Exception:
                tobj.timeout = True
                pass
            if not self.activeData:  # we don't have initial Map-Data yet
                loadMapAttempt += 1
                LOGGER.debug("Map-Content update attempt, but not active")
                if loadMapAttempt > self.maxLoadMapAttempts:
                    LOGGER.critical(
                        "Something is stopping the program of progressing. (Map-Attempts > {}\n"
                        "If this continues to happen, delete the Cache-File in \"{}\""
                        % (self.maxLoadMapAttempts, getVintelDir()))
                    exit(-1)
                continue
            if not self.active:
                LOGGER.debug("Ending {}" % self.name)
                return
            try:
                loadMapAttempt = 0
                if not tobj.timeout:  # not based on Timeout
                    if tobj.scrollPosition:
                        LOGGER.debug("Setting Map-Content start")
                        LOGGER.debug("Current Scroll-Position {}".format(tobj.scrollPosition))
                        tobj.zoomfactor = tobj.zoomFactor if tobj.zoomFactor else 1.
                        tobj.scrollTo = str("window.scrollTo({:.0f}, {:.0f});".
                                            format(tobj.scrollPosition.x() / tobj.zoomfactor,
                                                   tobj.scrollPosition.y() / tobj.zoomfactor))
                        tobj.newContent = injectScrollPosition(tobj.content, tobj.scrollTo)
                        self.map_update.emit(tobj.newContent)
                        LOGGER.debug("Setting Map-Content complete")
                else:
                    pass
            except Exception as e:
                LOGGER.error("Problem with setMapContent: %r", e)

    def quit(self):
        self.active = False
        LOGGER.debug("Stopping Map-Thread")


class AvatarFindThread(Thread, QObject):
    avatar_update = pyqtSignal(ChatEntryWidget, bytes)

    def __init__(self):
        Thread.__init__(self, name="AvatarFind")
        QObject.__init__(self)
        LOGGER.debug("Starting Avatar-Thread")
        self.queue = SixQueue.Queue()
        self.active = True
        self.wait = 300  # time between 2 requests in ms

    def addChatEntry(self, chatEntry, clearCache=False):
        try:
            if clearCache:
                cache = Cache()
                cache.removeAvatar(chatEntry.message.user)
            # Enqeue the data to be picked up in run()
            self.queue.put(chatEntry)
        except Exception as e:
            LOGGER.error("Error in AvatarFindThread: %r", e)

    def run(self):
        tobj = local()
        while True:
            try:
                tobj.lastCall = 0
                try:# Block waiting for addChatEntry() to enqueue something
                    tobj.chatEntry = self.queue.get(False)
                except Exception as e:
                    if not self.active:
                        LOGGER.debug("Ending {}" % self.name)
                        return
                    if e:
                        continue

                tobj.charname = tobj.chatEntry.message.user
                LOGGER.debug("AvatarFindThread getting avatar for %s" % tobj.charname)
                tobj.avatar = None
                if tobj.charname == "VINTEL":
                    with open(resourcePath("logo_small.png"), "rb") as tobj.f:
                        tobj.avatar = tobj.f.read()
                if not tobj.avatar:
                    tobj.diffLastCall = time.time() - tobj.lastCall
                    if tobj.diffLastCall < self.wait:
                        time.sleep((self.wait - tobj.diffLastCall) / 1000.0)
                    tobj.lastCall = time.time()
                    tobj.avatar = EsiHelper().getAvatarByName(tobj.charname)
                if tobj.avatar:
                    LOGGER.debug("AvatarFindThread emit avatar_update for %s" % tobj.charname)
                    self.avatar_update.emit(tobj.chatEntry, tobj.avatar)
                else:
                    LOGGER.debug("AvatarFindThread Avator not found for %s" % tobj.charname)
            except Exception as e:
                LOGGER.error("Error in AvatarFindThread : %r", e)

    def quit(self):
        self.active = False
        LOGGER.debug("Stopping Avatar-Thread")
        # if self.active:
        #     self.queue.put(None)
        # super(__class__, self).quit()


class KOSCheckerThread(Thread, QObject):
    kos_result = pyqtSignal(str, int, bool)

    def __init__(self):
        Thread.__init__(self, name="KOSChecker")
        QObject.__init__(self)
        LOGGER.debug("Starting KOSChecker-Thread")
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
            LOGGER.error("Error in KOSCheckerThread.addRequest: %r", e)

    def run(self):
        while True:
            # Block waiting for addRequest() to enqueue something
            names, requestType, onlyKos = self.queue.get(False)
            if not self.active:
                return
            try:
                # LOGGER.info("KOSCheckerThread kos checking %s" %  str(names))
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
                LOGGER.error("Error in KOSCheckerThread.run: %r", e)
                continue

            LOGGER.info("KOSCheckerThread emitting kos_result for: state = {0}, "
                        "text = {1}, requestType = {2}, hasKos = {3}".format("ok", text,
                                                                             requestType, hasKos))
            self.kos_result.emit(text, requestType, hasKos)
            # self.emit(PYQT_SIGNAL("kos_result"), "ok", text, requestType, hasKos)

    def quit(self):
        self.active = False
        LOGGER.debug("Stopping KOSChecker-Thread")


class MapStatisticsThread(Thread, QObject):
    statistic_data_update = pyqtSignal(dict)

    def __init__(self):
        Thread.__init__(self, name="MapStatistic")
        QObject.__init__(self)
        LOGGER.debug("Starting MapStatistics-Thread")
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
            req = self.queue.get(False)
            if not self.active:
                return
            if req != 1:
                continue
            self.refreshTimer.stop()
            LOGGER.debug("MapStatisticsThread requesting statistics")
            try:
                statistics = EsiHelper().getSystemStatistics()
                requestData = {"result": "ok", "statistics": statistics}
            except Exception as e:
                LOGGER.error("Error in MapStatisticsThread: %r", e)
                requestData = {"result": "error", "text": six.text_type(e)}
            self.lastStatisticsUpdate = time.time()
            self.refreshTimer.start(self.pollRate)
            self.statistic_data_update.emit(requestData)
            LOGGER.debug("MapStatisticsThread emitted statistic_data_update")

    def quit(self):
        self.active = False
        LOGGER.debug("Stopping MapStatistics-Thread")


class FileWatcherThread(Thread, QObject):
    file_change = pyqtSignal(str)

    def __init__(self, folder, maxAge=FILE_DEFAULT_MAX_AGE):
        Thread.__init__(self, name="FileWatcher")
        QObject.__init__(self)
        LOGGER.debug("Starting FileWatcher-Thread")
        self.folder = folder
        self.active = True
        self._warned = False
        self.maxAge = maxAge
        self.scan_delay = 500  # ms
        self.maxFiles = 200
        # index = Folder, content = {path, os.stat}
        self.filesInFolder = {}
        self._addFiles(folder)

    def addPath(self, path):
        self._addFiles(path)

    def run(self):
        while True:
            # don't overload the disk scanning
            time.sleep(self.scan_delay / 1000)
            # here, periodically, we check if any files have been added to the folder
            if self.active:
                self._scanPaths()
                for path in self.filesInFolder.keys():  # dict
                    self.filesInFolder[path] = self._checkChanges(
                        list(self.filesInFolder[path].items()))
            else:
                return

    def quit(self) -> None:
        self.active = False
        LOGGER.debug("Stopping FileWatcher-Thread")
        # self.thread().exit()

    def fileChanged(self, path):
        self.file_change.emit(path)

    def _sendWarning(self, path, length):
        # only do this ONCE at startup
        if self._warned:
            return
        LOGGER.warning(
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
                LOGGER.warning("Filewatcher-Thread error on \"%s\": %r", file, e)
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
        folderContent = sorted(glob.glob(os.path.join(path, "*")), key=os.path.getmtime,
                               reverse=True)
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
