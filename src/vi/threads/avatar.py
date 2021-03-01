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
import logging
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal
from six.moves import queue as SixQueue

from vi.cache.cache import Cache
from vi.chat.chatentrywidget import ChatEntryWidget
from vi.esi.esihelper import EsiHelper
from vi.stopwatch.mystopwatch import ViStopwatch as Stopwatch
from vi.resources import get_resource_path


class AvatarThread(QThread):
    avatar_update = pyqtSignal(ChatEntryWidget, bytes)

    def __init__(self):
        super().__init__()
        self.queue = SixQueue.Queue()
        self.LOGGER = logging.getLogger(__name__)
        self._active = False
        self.avatar_timeout = 2  # maximum time it should take
        self.avatar_retry_delay = 120  # try again after x seconds
        self.last_try = None
        self.sw = Stopwatch()
        self.cache = Cache()

    def add_chat_entry(self, chat_entry=None, clear_cache=False):
        try:
            if clear_cache:
                cache = Cache()
                cache.delete_avatar(chat_entry.message.user)

            # Enqeue the data to be picked up in run()
            self.queue.put(chat_entry)
        except Exception as e:
            self.LOGGER.error("Error in AvatarFindThread: %r", e)

    def start(self, priority: "QThread.Priority" = QThread.NormalPriority) -> None:
        self.LOGGER.debug("Starting Avatar-Thread")
        self._active = True
        super().start(priority)

    def switch_off_avatar(self):
        duration = self.sw.root_time()

        if duration and self.last_try:
            if duration * 1000 > self.avatar_timeout:
                self.LOGGER.info(
                    "Fetching Avatar took longer than %ds. Suspending a bit...",
                    self.avatar_timeout,
                )
                self.last_try = datetime.now()
        elif not duration:
            if datetime.now() - self.last_try > self.avatar_timeout:
                self.LOGGER.info("Re-Instating fetching Avatars...")
                self.last_try = None

    def run(self):
        while self._active:
            try:
                # Block waiting for add_chat_entry() to enqueue something
                chat_entry = self.queue.get()
                if not self._active:
                    return

                charname = chat_entry.message.user
                avatar = None
                if charname == "VINTEL":
                    with open(get_resource_path("logo_small.png"), "rb") as f:
                        avatar = f.read()
                if avatar is None and not self.last_try:
                    # TODO: Seems this causes issues of performance if bad internet connection...
                    #  try to do it with increasing time to skip Avatar-Load
                    #  or even do it within ESI to skip all calls!
                    with self.sw.timer("Avatar fetch"):
                        avatar = self.cache.get_avatar(charname)
                        if not avatar:
                            avatar = EsiHelper().get_avatarByName(charname)
                            if avatar:
                                self.cache.put_avatar(charname, avatar)
                    self.switch_off_avatar()
                if avatar:
                    self.LOGGER.debug(
                        "AvatarFindThread emit avatar_update for '%s': %s",
                        charname,
                        self.sw.get_report(),
                    )
                    self.avatar_update.emit(chat_entry, avatar)
                else:
                    self.LOGGER.warning(
                        'AvatarFindThread Avatar not found for "%s": %s',
                        charname,
                        self.sw.get_report(),
                    )
            except Exception as e:
                self.LOGGER.error("Error in AvatarFindThread : %r", e)

    def quit(self):
        if self._active:
            self.LOGGER.debug("Stopping Avatar-Thread")
            self._active = False
            self.add_chat_entry()
            super().quit()
