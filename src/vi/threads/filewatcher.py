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
from PyQt5.QtCore import QThread, pyqtSignal


class FileWatcherThread(QThread):
    file_change = pyqtSignal(str)
    file_removed = pyqtSignal(str)
    FILE_DEFAULT_MAX_AGE = 60 * 60 * 4  # oldest Chatlog-File to scan (4 hours)

    def __init__(self, folder, scan_interval: float = 0.5):
        super().__init__()
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.debug("Starting FileWatcher-Thread")
        self.folder = folder
        self._active = True
        self._warned = False
        self.scanInterval = scan_interval
        self.maxFiles = 200
        self.files_in_folder = {}
        self._add_files(folder)

    @property
    def max_age(self):
        return self.FILE_DEFAULT_MAX_AGE

    def add_path(self, path):
        self._add_files(path)

    def start(self, priority: "QThread.Priority" = QThread.NormalPriority) -> None:
        self.LOGGER.debug("Starting FileWatcher-Thread")
        self._active = True
        super().start(priority)

    def run(self):
        while self._active:
            # don't overload the disk scanning
            time.sleep(self.scanInterval)
            # here, periodically, we check if any files have been added to the folder
            self._scan_paths()
            for path in self.files_in_folder.keys():  # dict
                self.files_in_folder[path] = self._check_changes(
                    list(self.files_in_folder[path].items())
                )

    def quit(self) -> None:
        if self._active:
            self._active = False
            self.LOGGER.debug("Stopping FileWatcher-Thread")
            super().quit()

    def file_changed(self, path):
        self.file_change.emit(path)

    def remove_file(self, path):
        self.LOGGER.debug(
            "removing old File from tracking (older than %ds): %s",
            self.max_age, path
        )
        self.file_removed.emit(path)

    def _send_warning(self, path, length):
        # only do this ONCE at startup
        if self._warned:
            return
        self.LOGGER.warning(
            'Log-Folder "%s" has more than %d files (actually has %d)! This will impact performance! Consider tidying up!'
            % (path, self.maxFiles, length,)
        )
        self._warned = True

    def _check_changes(self, check_list):
        file_list = {}

        for file, file_stat in check_list:
            # might be tidying up..., so try
            try:
                path_stat = os.stat(file)
                if path_stat != file_stat:
                    self.file_changed(file)
                file_list[file] = path_stat
            except Exception as e:
                self.LOGGER.warning('File-Stat-Error on "%s": %r', file, e,)
                pass
        return file_list

    # scan all configured paths
    def _scan_paths(self):
        self._add_files(self.folder)

    # check for new files in folder and add if necessary
    # TODO: to filter chat-logs which are kept open over a long time, match it to character...
    #  new log-file for character, close old one
    def _add_files(self, path: str = None):
        if not path:
            self.LOGGER.warning("No path passed to _addFiles !")
        files_in_dir = (
            self.files_in_folder[path]
            if path and path in self.files_in_folder.keys()
            else {}
        )
        changed = False
        now = time.time()
        # order by date descending
        try:
            folder_content = sorted(
                glob.glob(os.path.join(path, "*")), key=os.path.getmtime, reverse=True
            )
        except:
            # might be tidying up in the background
            folder_content = []
        if self.maxFiles and len(folder_content) > self.maxFiles:
            self._send_warning(path, len(folder_content))
        for fullPath in folder_content:
            try:
                path_stat = os.stat(fullPath)
                # this file currently not logged
                if fullPath not in files_in_dir:
                    if not stat.S_ISREG(path_stat.st_mode):
                        continue
                    if self.max_age and ((now - path_stat.st_mtime) > self.max_age):
                        # we now BREAK, since not interested in older files
                        break
                    files_in_dir[fullPath] = path_stat
                    changed = True
                # this file now older than wanted
                elif self.max_age and (now - path_stat.st_mtime) > self.max_age:
                    # files_in_dir.pop(fullPath)
                    self.remove_file(fullPath)
                    changed = True
                    del files_in_dir[fullPath]
            except Exception as e:
                self.LOGGER.error(
                    "Trying to remove %s from dictionary %r: %r",
                    fullPath, files_in_dir,
                    e,
                )
                pass
        if changed:
            self.files_in_folder[path] = files_in_dir
            self.LOGGER.debug(
                "currently tracking %d files in %s", len(files_in_dir), path,
            )
            self.LOGGER.debug("  %r", self.files_in_folder[path],)
