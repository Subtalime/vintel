###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
# 																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
# 																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
# 																		  #
# 																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import logging

from six.moves import queue as SixQueue
import queue
from PyQt5.QtCore import QThread, pyqtSignal


class ChatTidyUpThread(QThread):
    time_up = pyqtSignal()

    def __init__(self, max_age: int = 20 * 60, interval: float = 60):
        super().__init__()
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.debug("Starting ChatTidy-Thread")
        self._active = False
        self.interval = interval
        self.max_age = max_age
        self.queue = SixQueue.Queue(maxsize=1)

    def start(self, priority: "QThread.Priority" = QThread.NormalPriority) -> None:
        self.LOGGER.debug("Starting Chat-Tidy-Up-Thread")
        self._active = True
        super().start(priority)

    def run(self):
        while self._active:
            try:
                self.queue.get(timeout=self.interval)
            except queue.Empty as e:
                pass
            if self._active:
                self.time_up.emit()

    def quit(self):
        if self._active:
            self.LOGGER.debug("Stopping ChatTidy-Thread")
            self._active = False
            self.queue.put(1)
            super().quit()
