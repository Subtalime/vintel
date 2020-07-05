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
from time import time
from queue import Queue
from atexit import register
from logging import LogRecord, getLogger
from logging.handlers import QueueHandler, QueueListener
from threading import RLock

_lock = RLock()


def _acquire_lock():
    """
    Acquire the module-level lock for serializing access to shared data.
    This should be released with _releaseLock().
    """
    if _lock:
        _lock.acquire()


def _release_lock():
    """
    Release the module-level lock acquired by calling _acquireLock().
    """
    if _lock:
        _lock.release()


class LogQueueHandler(QueueHandler):
    tidySize = 5000  # number of messages to hold in buffer
    pruneDelay = 60 * 60

    def __init__(
        self, handlers, respect_handler_level=False, auto_run=True, queue=Queue(-1)
    ):
        super().__init__(queue)
        self.queue = queue
        self._listener = QueueListener(
            self.queue, *handlers, respect_handler_level=respect_handler_level
        )
        if auto_run:
            self.start()
            register(self.stop)

        self.pruneTime = time()
        self._tidying = False
        # Log-Messages stored here
        self.log_records = []

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()

    def emit(self, record: LogRecord) -> None:
        self.store(record)
        return super().emit(record)

    def store(self, record: LogRecord):
        # seems we don't need any of this with a QueueHandler
        pass
        self.log_records.append(record)
        self.prune()

    def prune(self):
        if not self._tidying and self.pruneTime + self.pruneDelay < time():
            self.pruneTime = time()
            try:
                _acquire_lock()
                self._tidying = True
                getLogger().debug("LogWindow Tidy-Up start")
                del self.log_records[: len(self.log_records) - self.tidySize]
            except Exception as e:
                getLogger().error("Error in Tidy-Up of Log-Window", e)
            finally:
                _release_lock()
                self._tidying = False
                getLogger().debug("LogWindow Tidy-Up complete")
