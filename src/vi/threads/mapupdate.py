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

import queue
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, pyqtSignal
from vi.resources import getVintelDir
from vi.settings.settings import GeneralSettings


class MapUpdateThread(QThread):
    map_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.debug("Starting MapUpdate Thread ")
        self.queue = queue.Queue()
        self._active = False
        self.paused = False

    def addToQueue(self, content=None, zoomfactor=None, scrollposition=None):
        self.queue.put((content, zoomfactor, scrollposition))

    def start(self, priority: QThread.Priority = QThread.NormalPriority) -> None:
        self.LOGGER.debug("Run-Starting MapUpdate Thread")
        self._active = True
        super().start(priority)

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
                content, zoom_factor, scroll_position = self.queue.get(
                    timeout=GeneralSettings().map_update_interval / 1000
                )
            except queue.Empty:
                if self.paused:  # we don't have initial Map-Data yet
                    load_map_attempt += 1
                    self.LOGGER.debug("Map-Content update attempt, but not active")
                    if load_map_attempt > 10:
                        self.LOGGER.critical(
                            "Something is stopping the program of progressing. (Map-Attempts > 10\n"
                            'If this continues to happen, delete the Cache-File in "%s"'
                            % (getVintelDir(),)
                        )
                        self.quit()
                        return
                load_map_attempt = 0
                continue
            if content:  # not based on Timeout
                self.LOGGER.debug("Setting Map-Content start")
                zoom_factor = zoom_factor if zoom_factor else 1.0
                scroll_to = ""
                if scroll_position:
                    self.LOGGER.debug(
                        "Current Scroll-Position {}".format(scroll_position)
                    )
                    scroll_to = str(
                        "window.scrollTo({:.0f}, {:.0f});".format(
                            scroll_position.x() / zoom_factor,
                            scroll_position.y() / zoom_factor,
                        )
                    )
                new_content = injectScrollPosition(content, scroll_to)
                self.map_update.emit(new_content)
                self.LOGGER.debug("Setting Map-Content complete")

    def quit(self):
        if self._active:
            self.LOGGER.debug("Stopping MapUpdate Thread")
            self._active = False
            self.pause(False)
            self.addToQueue()
            super().quit()

