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
import six

from six.moves import queue as SixQueue
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from vi.esi.esihelper import EsiHelper


class StatisticsThread(QThread):
    STATISTICS_UPDATE_INTERVAL_MSECS = (1 * 60) * 1000  # every hour
    statistic_data_update = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.debug("Starting MapStatistics-Thread")
        self.queue = SixQueue.Queue(maxsize=1)
        self.refresh_timer = None
        self._active = False

    @property
    def poll_rate(self):
        return self.STATISTICS_UPDATE_INTERVAL_MSECS

    def _request_statistics(self):
        self.queue.put(1)

    def start(self, priority: "QThread.Priority" = QThread.NormalPriority) -> None:
        self.LOGGER.debug("Starting Map-Statistic-Update-Thread")
        self._active = True
        super().start(priority)

    def run(self):
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._request_statistics)
        while self._active:
            # Block waiting for _request_statistics() to enqueue a token
            self.queue.get()
            if not self._active:
                return
            self.refresh_timer.stop()
            self.LOGGER.debug("requesting statistics")
            try:
                statistics = EsiHelper().getSystemStatistics()
                request_response = {"result": "ok", "statistics": statistics}
            except Exception as e:
                self.LOGGER.error("Error in MapStatisticsThread: %r", e)
                request_response = {"result": "error", "text": six.text_type(e)}
            self.refresh_timer.start(self.poll_rate)
            self.statistic_data_update.emit(request_response)
            self.LOGGER.debug("emitted statistic_data_update")

    def quit(self):
        if self._active:
            self.LOGGER.debug("Stopping MapStatistics-Thread")
            self._active = False
            self._request_statistics()
            super().quit()

