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
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from vi.resources import getVintelLogDir

class MyDateFormatter(logging.Formatter):
    import datetime as dt
    converter = dt.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s

def construct_logfilepath(loader, node):
    value = loader.construct_scalar(node)
    return os.path.join(getVintelLogDir(), value)

class LogConfiguration:
    LOG_CONFIG = "logging.yaml"
    MAX_FILE_SIZE = 1024 * 1024 * 5
    MAX_FILE_COUNT = 7

    def __init__(self, config_file=LOG_CONFIG, log_folder="."):
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   config_file) if not os.path.exists(config_file) else config_file

        if os.path.exists(config_path):
            with open(config_path, "rt") as f:
                try:
                    yaml.add_constructor(u'!log_path', construct_logfilepath)
                    config = yaml.load(f)
                    # try reading as dictionary
                    logging.config.dictConfig(config)
                except ImportError:
                    try:
                        # next attempt INI-File format
                        logging.config.fileConfig(config_path, disable_existing_loggers=False)
                    except Exception as e:
                        # OK, I give up
                        print(e)
                        raise
                except Exception as e:
                    print(e)
                    raise
        else:
            self.default(log_folder=log_folder)


    def default(self, log_level=logging.INFO, log_folder="."):
        # just in case any loggers are currently active
        logging.shutdown()

        rootLogger = logging.getLogger()
        rootLogger.setLevel(log_level)

        # Setup logging for console and rotated log files
        formatter = MyDateFormatter(
            fmt='%(asctime)s|%(levelname)s [%(threadName)s(%(thread)d)] (%(filename)s/%(funcName)s/%(lineno)d): %(message)s',
            datefmt='%d/%m %H:%M:%S.%f')

        logFilename = os.path.join(log_folder, "output.log")
        fileHandler = RotatingFileHandler(maxBytes=self.MAX_FILE_SIZE,
                                          backupCount=self.MAX_FILE_COUNT, filename=logFilename,
                                          mode='a')
        fileHandler.setFormatter(formatter)
        # in the log file, ALWAYS debug
        fileHandler.setLevel(logging.DEBUG)
        rootLogger.addHandler(fileHandler)

        # stdout
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        consoleHandler.setLevel(log_level)
        rootLogger.addHandler(consoleHandler)


if __name__ == "__main__":
    log = LogConfiguration()
