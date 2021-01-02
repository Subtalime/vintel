#  Vintel - Visual Intel Chat Analyzer
#  Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
import os
import logging
import yaml
import threading
import queue
import six
import sys
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler
from vi.logger.logwindow import LogDisplayHandler, LOG_WINDOW_HANDLER_NAME
from vi.logger.logqueue import LogQueueHandler
from vi.resources import getVintelLogDir, resourcePath
from vi.singleton import Singleton
from vi.version import ROOT_DIR


class MyDateFormatter(logging.Formatter):
    import datetime as dt

    converter = dt.datetime.fromtimestamp

    def formatTime(self, record, date_format=None):
        ct = self.converter(record.created)
        if date_format:
            s = ct.strftime(date_format)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


class LogConfiguration(six.with_metaclass(Singleton)):
    LOG_CONFIG = "logging.yaml"
    MAX_FILE_SIZE = 1024 * 1024 * 5
    MAX_FILE_COUNT = 7
    LOG_FILE_PATH = None


    def construct_logfilepath(self, loader, node):
        value = loader.construct_scalar(node)
        return os.path.join(self.log_folder, value)

    def __init__(self, config_file=LOG_CONFIG, log_folder=None):
        # TODO: Try and set up the Queue-Handler
        # TODO: Then open the LogWindows which should attach to the Queue-Handler as Queue-Listener
        # TODO: see https://stackoverflow.com/questions/58592557/how-to-wrap-python-logging-module
        # TODO: also see below TODO!
        path = os.path.split(config_file)
        if path[0] == "":
            config_path = self._getDefaultLogConfigFilePath(config_file)
        else:
            config_path = config_file
        self.log_folder = log_folder if log_folder is not None else getVintelLogDir()
        if os.path.exists(config_path):
            with open(config_path, "rt") as f:
                try:
                    # if there is a variable in the configuration, replace it
                    yaml.add_constructor(u"!log_path", self.construct_logfilepath)
                    # Loader MUST be specified, otherwise constructor wont work!
                    config = yaml.load(f, Loader=yaml.Loader)
                    # try reading as dictionary
                    logging.config.dictConfig(config)
                    # success
                    f = config['handlers'].get('file').get('filename')
                    if f:
                        LogConfiguration.LOG_FILE_PATH = f
                    self.LOG_CONFIG = config_path
                except ImportError:
                    try:
                        # next attempt INI-File format
                        try:
                            logging.config.fileConfig(
                                config_path, disable_existing_loggers=True
                            )
                        except:
                            self.default(log_folder=self.log_folder)
                    except Exception as e:
                        # OK, I give up
                        print(e)
                        raise
                except Exception as e:
                    self.default(log_folder=self.log_folder)
                    # print(e)
                    # raise
        else:
            self.default(log_folder=self.log_folder)

    def _getDefaultLogConfigFilePath(self, config_file: str = LOG_CONFIG) -> str:
        return os.path.join(ROOT_DIR, config_file)

    def default(self, log_level=logging.INFO, log_folder="."):
        # just in case any loggers are currently active
        # logging.shutdown()

        rootLogger = logging.getLogger()
        rootLogger.setLevel(log_level)

        # Setup logging for console and rotated log files
        formatter = MyDateFormatter(
            fmt="%(asctime)s|%(levelname)s [%(threadName)s(%(thread)d)] (%(filename)s/%(funcName)s/%(lineno)d): %(message)s",
            datefmt="%d/%m %H:%M:%S.%f",
        )

        logFilename = os.path.join(log_folder, "vintel_default.log")
        fileHandler = RotatingFileHandler(
            maxBytes=self.MAX_FILE_SIZE,
            backupCount=self.MAX_FILE_COUNT,
            filename=logFilename,
            mode="a",
            encoding="utf-8",
        )
        self.LOG_FILE_PATH = logFilename
        fileHandler.setFormatter(formatter)
        # in the log file, ALWAYS debug
        fileHandler.setLevel(logging.DEBUG)

        queue_handlers = [fileHandler]
        # stdout
        # only if running from Dev-Environment
        if not getattr(sys, "frozen", False):
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(formatter)
            consoleHandler.setLevel(log_level)
            # rootLogger.addHandler(consoleHandler)
            queue_handlers.append(consoleHandler)

        logQueue = LogQueueHandler(queue_handlers)
        rootLogger.addHandler(logQueue)


class LogConfigurationThread(threading.Thread):
    def __init__(self, log_window=None, **kwargs):
        threading.Thread.__init__(self, *kwargs)
        self.queue = queue.Queue()
        self.LOGGER = logging.getLogger(__name__)
        self.timeout = 5
        self.active = True
        self.file_stat = None
        self._logWindow = log_window

    def run(self) -> None:
        while self.active:
            try:
                self.queue.get(timeout=self.timeout)
            except queue.Empty as e:
                pass
            # LOG_FILEPATH is real... but still catch, in case it has been moved/deleted
            if LogConfiguration.LOG_CONFIG:
                if not self.file_stat:
                    try:
                        self.file_stat = os.stat(LogConfiguration.LOG_CONFIG)
                    except FileNotFoundError:
                        pass
                if self.file_stat:
                    new_stat = os.stat(LogConfiguration.LOG_CONFIG)
                    if new_stat != self.file_stat:
                        self.file_stat = new_stat
                        try:
                            self.LOGGER.debug(
                                'Configuration-Change in "%s"',
                                LogConfiguration.LOG_CONFIG,
                            )
                            LogConfiguration(LogConfiguration.LOG_CONFIG)
                            # Make sure our LogWindowHandler is still alive!
                            if LOG_WINDOW_HANDLER_NAME not in logging._handlerList:
                                if self._logWindow:
                                    self._logWindow.addHandler(LogDisplayHandler())
                            self.LOGGER.debug("Configuration-Change applied")
                        except Exception as e:
                            self.LOGGER.error("Error in Configuration! %r", e)
                            pass

    def quit(self) -> None:
        self.active = False
        self.queue.put(0)


if __name__ == "__main__":


    LOGGER = logging.getLogger()
    LogConfiguration(config_file="./logging.yaml", log_folder=".")
    # log = LogConfiguration()

    LOGGER.critical("Test")
    LOGGER.error("Test")
    LOGGER.warning("Test")
    LOGGER.info("Test")
    LOGGER.debug("Test")
