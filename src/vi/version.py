import requests, logging
from PyQt5.QtCore import pyqtSignal, QThread
from packaging.version import parse

VERSION = "1.2.0"
SNAPSHOT = True # set to false when releasing
URL = "https://github.com/Subtalime/vintel"
PROGNAME = "Vintel"
DISPLAY = PROGNAME + " " + VERSION + "{dev}".format(dev="-SNAPSHOT" if SNAPSHOT else "")

def getNewestVersion():
    try:
        url = u"http://vintel.tschache.com/resources/current_version.txt"
        newestVersion = requests.get(url).text
        return newestVersion
    except Exception as e:
        logging.error("Failed version-request: %s", e)
        return "0.0"


class NotifyNewVersionThread(QThread):
    newer_version = pyqtSignal(str)

    def __init__(self):
        QThread.__init__(self)
        logging.debug("Starting Version-Thread")
        self.alerted = False


    def run(self):
        if not self.alerted:
            try:
                # Is there a newer version available?
                newestVersion = getNewestVersion()
                if newestVersion and parse(newestVersion) > parse(VERSION):
                    self.newer_version.emit(newestVersion)
                    self.alerted = True
            except Exception as e:
                logging.error("Failed NotifyNewVersionThread: %s", e)

    def quit(self) -> None:
        logging.debug("Stopping Version-Thread")
        QThread.quit(self)
