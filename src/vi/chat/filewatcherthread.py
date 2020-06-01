#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
import time
import logging
import os
import stat
import glob
from PyQt5.QtCore import QThread, QTimer, pyqtSignal

FILE_DEFAULT_MAX_AGE = 60 * 60 * 4  # oldest Chatlog-File to scan (4 hours)


class FileWatcherThread(QThread):
    file_change = pyqtSignal(str)
    file_removed = pyqtSignal(str)

    def __init__(self, folder, maxAge=FILE_DEFAULT_MAX_AGE, scan_interval: float = 0.5):
        super(__class__, self).__init__()
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.debug("Starting FileWatcher-Thread")
        self.folder = folder
        self._active = True
        self._warned = False
        self.maxAge = maxAge
        self.scanInterval = scan_interval
        self.maxFiles = 200
        # index = Folder, content = {path, os.stat}
        self.filesInFolder = {}
        self._addFiles(folder)

    def addPath(self, path):
        self._addFiles(path)

    def start(self, priority: "QThread.Priority" = QThread.NormalPriority) -> None:
        self.LOGGER.debug("Starting FileWatcher-Thread")
        self._active = True
        super(FileWatcherThread, self).start(priority)

    def run(self):
        while self._active:
            # don't overload the disk scanning
            time.sleep(self.scanInterval)
            # here, periodically, we check if any files have been added to the folder
            if self._active:
                self._scanPaths()
                for path in self.filesInFolder.keys():  # dict
                    self.filesInFolder[path] = self._checkChanges(
                        list(self.filesInFolder[path].items())
                    )

    def quit(self) -> None:
        if self._active:
            self._active = False
            self.LOGGER.debug("Stopping FileWatcher-Thread")
            super(FileWatcherThread, self).quit()

    def fileChanged(self, path):
        self.file_change.emit(path)

    def removeFile(self, path):
        self.LOGGER.debug(
            "removing old File from tracking (older than %d seconds): %s"
            % (self.maxAge, path,)
        )
        self.file_removed.emit(path)

    def _sendWarning(self, path, length):
        # only do this ONCE at startup
        if self._warned:
            return
        self.LOGGER.warning(
            'Log-Folder "%s" has more than %d files (actually has %d)! This will impact performance! Consider tidying up!'
            % (path, self.maxFiles, length,)
        )
        self._warned = True

    def _checkChanges(self, check_list):
        file_list = {}

        for file, fstat in check_list:
            # might be tidying up..., so try
            try:
                pathStat = os.stat(file)
                if pathStat != fstat:
                    fstat = pathStat
                    self.fileChanged(file)
                file_list[file] = fstat
            except Exception as e:
                self.LOGGER.warning('Filewatcher-Thread error on "%s": %r' % (file, e,))
                pass
        return file_list

    # scan all configured paths
    def _scanPaths(self):
        self._addFiles(self.folder)
        # for path in self.filesInFolder.keys():
        #     self._addFiles(path)

    # check for new files in folder and add if necessary
    # TODO: to filter chat-logs which are kept open over a long time, match it to character...
    #  new log-file for character, close old one
    def _addFiles(self, path: str = None):
        if not path:
            self.LOGGER.warning("No path passed to _addFiles !")
        files_in_dir = (
            self.filesInFolder[path]
            if path and path in self.filesInFolder.keys()
            else {}
        )
        changed = False
        now = time.time()
        # order by date descending
        try:
            folderContent = sorted(
                glob.glob(os.path.join(path, "*")), key=os.path.getmtime, reverse=True
            )
        except:
            # might be tidying up in the background
            folderContent = ()
        if self.maxFiles and len(folderContent) > self.maxFiles:
            self._sendWarning(path, len(folderContent))
        for fullPath in folderContent:
            try:
                path_stat = os.stat(fullPath)
                # this file currently not logged
                if fullPath not in files_in_dir:
                    if not stat.S_ISREG(path_stat.st_mode):
                        continue
                    if self.maxAge and ((now - path_stat.st_mtime) > self.maxAge):
                        # we now BREAK, since not interested in older files
                        break
                    files_in_dir[fullPath] = path_stat
                    changed = True
                # this file now older than wanted
                elif self.maxAge and (now - path_stat.st_mtime) > self.maxAge:
                    # files_in_dir.pop(fullPath)
                    self.removeFile(fullPath)
                    changed = True
                    del files_in_dir[fullPath]
            except Exception as e:
                self.LOGGER.error(
                    "Trying to remove %s from dictionary %r"
                    % (fullPath, files_in_dir,),
                    e,
                )
                pass
        if changed:
            self.filesInFolder[path] = files_in_dir
            self.LOGGER.debug(
                "currently tracking %d files in %s" % (len(files_in_dir), path,)
            )
            self.LOGGER.debug("  %r" % (self.filesInFolder[path],))
