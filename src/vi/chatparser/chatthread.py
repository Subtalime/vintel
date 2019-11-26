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

import logging
import datetime
import six
import os
import asyncio
from vi.dotlan import mysystem as systems
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from queue import Queue
from threading import Thread
from vi.character.Characters import Characters
from vi.chatparser.chatmessage import Message
from vi.chatparser.parser_functions import parseCharnames, parseShips, parseStatus, parseSystems, parseUrls
from vi import states
from vi.singleton import Singleton

LOGGER = logging.getLogger(__name__)

__all_known_messages = []


def AllMessagesAdd(message: Message) -> bool:
    if message in __all_known_messages:
        return False
    __all_known_messages.append(message)
    return True


def AllMessagesContains(message: Message):
    return message in __all_known_messages


LOCAL_NAMES = ("Local", "Lokal",
               six.text_type("\u041B\u043E\u043A\u0430\u043B\u044C\u043D\u044B\u0439"))

'''
on change of a log-file, currently viui comes to a standstill, while the log-file is being
parsed for any significant messages which need to be pushed to the system.
This thread is an attempt, to handle the Log-File change outside the UI, queue all the
result Messages and pop them on a Queue for the UI to pick up and send off 
Flow:
- Create THIS (main Thread) listening for changes in Log-Files being emitted, on each "emit"
  a new Thread gets created to handle the Log-File process. This way, multiple files can 
  change at the same time and not stop any other processes from doing their stuff. This means
  that a separate Thread is created per Log-File
- Log-File changed
-- create a new Chatwidget
-- populate the Widget with links
'''


class ChatThread(QThread):
    """
    Thread to react if the File-Watcher-Thread encounters any changes
    This will direct the change to the correct processing Thread-Queue
    """
    player_added = pyqtSignal(list)
    message_added = pyqtSignal(Message)
    message_updated = pyqtSignal(Message)

    def __init__(self, room_names: list, dotlan_systems: systems = {}, known_players: list = [], ship_parser=None,
                 character_parser=None):
        super(__class__, self).__init__()
        LOGGER.debug("Creating ChatThread")
        self.queue = Queue()
        self.active = True
        self.room_names = room_names
        self.dotlan_systems = dotlan_systems
        # ship_parser.connect(self._shipParser)
        # character_parser.connect(self._charParser)
        self.process_pool = {}
        self.known_players = known_players

    # if file changed or file newly discovered
    def addLogFile(self, file_path: str, remove: bool = False):
        self.queue.put((file_path, remove))

    def removeLogFile(self, file_path: str):
        self.addLogFile(file_path, remove=True)

    def updateRoomNames(self, room_names: list):
        self.room_names = room_names
        self._tidyLogs()

    def addCharacter(self, player_name):
        if player_name not in self.known_players:
            self.known_players.append(player_name)
            self.player_added.emit(self.known_players)

    def updateDotlanSystems(self, dotlan_systems: systems):
        self.dotlan_systems = dotlan_systems
        for thread in self.process_pool.keys():
            self.process_pool[thread].updateDotlanSystems(self.dotlan_systems)

    def _tidyLogs(self):
        for path in self.process_pool.keys():
            room = os.path.basename(path)[:-20]
            if room not in self.room_names:
                self.addLogFile(path, True)

    def messageAdded(self, message: Message):
        if AllMessagesAdd(message):
            self.message_added.emit(message)

    def messageUpdated(self, message: Message):
        # AllMessagesAdd(message)
        self.message_updated.emit(message)

    def _shipParser(self, value):
        pass

    def _charParser(self, value):
        pass

    def run(self):
        while self.active:
            logfile, delete = self.queue.get()
            if self.active:
                if logfile and logfile not in self.process_pool.keys() and not delete:
                    roomname = os.path.basename(logfile)[:-20]
                    if not roomname in self.room_names and not roomname in LOCAL_NAMES:
                        LOGGER.debug("Not interested in \"%s\" since not in monitored rooms", logfile)
                        continue
                    self.process_pool[logfile] = ChatThreadProcess(logfile, self.dotlan_systems)
                    self.process_pool[logfile].message_added.connect(self.messageAdded)
                    self.process_pool[logfile].message_updated.connect(self.messageUpdated)
                    self.process_pool[logfile].new_player.connect(self.addCharacter)
                    self.process_pool[logfile].start()
                if delete and logfile in self.process_pool.keys():
                    self.process_pool[logfile].quit()
                    self.process_pool.pop(logfile)
                elif not delete:
                    self.process_pool[logfile].logfileChanged()

    def quit(self):
        LOGGER.debug("Closing Chat-Thread")
        self.active = False
        self.addLogFile(None)
        for thread in self.process_pool.keys():
            self.process_pool[thread].quit()
        QThread.quit(self)


class ChatThreadProcess(QThread):
    new_player = pyqtSignal(str)
    message_added = pyqtSignal(Message)
    message_updated = pyqtSignal(Message)

    def __init__(self, log_file_path: str, dotlan_systems: systems = ()):
        super(__class__, self).__init__()
        self.queue = Queue()
        self.log_file = log_file_path
        # any messages older than this will be ignored
        self.message_age = 60
        self.active = True
        self.charname = None
        self.roomname = None
        self.session_start = None
        self.parsed_lines = 0
        self.local_room = False
        self.dotlan_systems = dotlan_systems
        self.knownMessages = []
        # locations of this character
        self.locations = []
        self.ship_scanner_enabled = True
        self.character_scanner_enabled = True
        self.worker_loop = asyncio.new_event_loop()
        self.worker = Thread(target=self._runLoop)
        self.worker.start()

    def updateDotlanSystems(self, dotlan_systems: systems):
        self.dotlan_systems = dotlan_systems

    def _refineMessage(self, message: Message):
        LOGGER.debug("Start refining message %s: %r", self.roomname, message)
        if self.ship_scanner_enabled:
            while parseShips(message.rtext):
                continue
        while parseUrls(message.rtext):
            continue
        if self.character_scanner_enabled:
            while parseCharnames(message.rtext):
                continue

        # If message says clear and no system? Maybe an answer to a request?
        if message.status == states.CLEAR and not message.systems:
            maxSearch = 2  # we search only max_search messages in the room
            for count, oldMessage in enumerate(oldMessage for oldMessage in
                                               self.knownMessages[-1::-1]
                                               if oldMessage.room == self.roomname):
                if oldMessage.systems and oldMessage.status == states.REQUEST:
                    for system in oldMessage.systems:
                        message.systems.append(system)
                    break
                if count > maxSearch:
                    break
        message.message = six.text_type(message.rtext)
        # multiple clients?
        self.knownMessages.append(message)
        if message.systems:
            for system in message.systems:
                system.messages.append(message)
        self.message_updated.emit(message)
        LOGGER.debug("Done refining message %s: %r", self.roomname, message)

    def _runLoop(self):
        asyncio.set_event_loop(self.worker_loop)
        self.worker_loop.run_forever()

    # get all the relevant information which ChatParser requires
    def _prepareParser(self) -> bool:
        LOGGER.debug("Analysing relevance of %s", self.log_file)
        filename = os.path.basename(self.log_file)
        self.roomname = filename[:-20]
        if self.roomname in LOCAL_NAMES:
            self.local_room = True
        lines = self._getLines()
        # for local-chats we need more infos
        for line in lines:
            if "Listener:" in line:
                self.charname = line[line.find(":") + 1:].strip()
            elif "Session started:" in line:
                sessionStr = line[line.find(":") + 1:].strip()
                self.session_start = datetime.datetime.strptime(sessionStr, "%Y.%m.%d %H:%M:%S")
            if self.charname and self.session_start:
                break
        if not self.charname or not self.session_start:
            LOGGER.warning("File did not contain relevant information: \"%s\"", self.log_file)
            return False
        # tell the world we're monitoring a new character
        self.new_player.emit(self.charname)
        # first 13 lines are Header information
        self.parsed_lines = 12
        # now head forward until you hit a timestamp, younger then max_age
        for line in lines[self.parsed_lines:]:
            timestamp, username, text = self._parseLine(line)
            if (datetime.datetime.now() - timestamp).total_seconds() <= self.message_age:
                break
            self.parsed_lines += 1
        LOGGER.debug("Registered %s in %s", self.charname, self.roomname)
        return True

    def _parseLine(self, line) -> tuple:
        # finding the timestamp
        timeStart = line.find("[") + 1
        timeEnds = line.find("]")
        timeStr = line[timeStart:timeEnds].strip()
        try:
            timestamp = datetime.datetime.strptime(timeStr, "%Y.%m.%d %H:%M:%S")
        except ValueError:
            LOGGER.error("Invalid Timestamp in \"{}\" Line {}".format(self.log_file, line))
            raise
        # finding the username of the poster
        userEnds = line.find(">")
        username = line[timeEnds + 1:userEnds].strip()
        # finding the pure message
        text = line[userEnds + 1:].strip()  # text will the text to work an
        return timestamp, username, text

    def _getLines(self) -> list:
        try:
            with open(self.log_file, "r", encoding='utf-16-le') as f:
                content = f.read()
            lines = content.split("\n")
        except Exception as e:
            LOGGER.error("Failed to read log file \"%s\" %r", self.log_file, e)
            raise e
        return lines

    def _processFile(self):
        lines = self._getLines()
        for line in lines[self.parsed_lines:]:
            line = line.strip()
            if len(line) > 2:
                if self.local_room:
                    message = self._parseLocal(line)
                else:
                    message = self._lineToMessage(line)
                if message:
                    # multiple clients?
                    if AllMessagesContains(message):
                        LOGGER.debug("Ignoring message (duplicate) from %s in %s", self.charname, self.roomname)
                        continue
                    # here, I believe, we should add it to the Widget-List and update
                    # the Map. Hence, we emit the Message
                    self.message_added.emit(message)
                    LOGGER.debug("%s: Notify new message: %r", self.roomname, message)
                    # Thereafter, the Worker-Loop can do the beautifying of the Widget
                    self.worker_loop.call_soon_threadsafe(self._refineMessage, message)
        self.parsed_lines = len(lines) - 1

    def _parseLocal(self, line) -> Message:
        """
        Parsing a line from the local chat. Can contain the system of the char
        """
        message = None
        if len(self.locations) == 0:
            self.locations = {"system": "?",
                              "timestamp": datetime.datetime(1970, 1, 1, 0, 0, 0, 0)}

        timestamp, username, text = self._parseLine(line)
        # anything older than max_age, ignore
        if (datetime.datetime.now() - timestamp).total_seconds() > self.message_age:
            LOGGER.debug("Message-Line too old")
            return None

        if username in ("EVE-System", "EVE System"):
            if ":" in text:
                system = text.split(":")[1].strip().replace("*", "").upper()
                status = states.LOCATION
            else:
                # We could not determine if the message was system-change related
                system = "?"
                status = states.IGNORE
            if timestamp > self.locations["timestamp"]:
                self.locations["system"] = system
                self.locations["timestamp"] = timestamp
                message = Message(self.roomname, text, timestamp, self.charname, currsystems=[system, ], status=status)
        return message

    def _lineToMessage(self, line) -> Message:
        timestamp, username, text = self._parseLine(line)
        message = None
        originalText = text
        formattedText = u"<rtext>{0}</rtext>".format(text)
        soup = BeautifulSoup(formattedText, 'html.parser')
        rtext = soup.select("rtext")[0]
        the_systems = set()
        upperText = text.upper()
        # anything older than max_age, ignore
        if (datetime.datetime.now() - timestamp).total_seconds() > self.message_age:
            LOGGER.debug("Message-Line too old")
            return None
        # KOS request
        if upperText.startswith("XXX "):
            message = Message(self.roomname, text, timestamp, username, rtext=rtext,
                              status=states.KOS_STATUS_REQUEST)
        elif self.roomname.startswith("="):
            message = Message(self.roomname, "xxx " + text, timestamp, username,
                              status=states.KOS_STATUS_REQUEST, rtext=rtext)
        elif upperText.startswith("VINTELSOUND_TEST"):
            message = Message(self.roomname, text, timestamp, username,
                              status=states.SOUND_TEST, rtext=rtext)
        else:
            parsedStatus = parseStatus(rtext)
            status = parsedStatus if parsedStatus is not None else states.ALARM
            message = Message(self.roomname, text, timestamp, username, status=status, rtext=rtext)
            while parseSystems(self.dotlan_systems, message.rtext, message.systems):
                continue
        LOGGER.debug("%s: Message created: %r", self.roomname, message)
        return message

    def logfileChanged(self, val=1):
        self.queue.put(val)

    def run(self):
        while self.active:
            if self.active and not self.charname:
                # unusable log-file... end thread
                if not self._prepareParser():
                    self.active = False
                    continue
            self.queue.get()
            # process the Log-File
            if self.active:
                self._processFile()

    def quit(self):
        LOGGER.debug("Closing Thread for %s in %s", self.charname, self.roomname)
        self.active = False
        self.logfileChanged(0)
        QThread.quit(self)


if __name__ == "__main__":
    from PyQt5.Qt import QApplication
    from vi.threads import FileWatcherThread
    from vi.resources import getEveChatlogDir, getVintelDir
    from vi.dotlan.mymap import MyMap
    from vi.cache import cache
    import sys
    from vi.esi import EsiInterface

    logging.getLogger(__name__).setLevel(logging.DEBUG)

    ship_parser_change = pyqtSignal(bool)
    char_parser_change = pyqtSignal(bool)
    rooms = ("testbov")
    # rooms = ("delve.imperium", "querious.imperium", "testbov")
    path_to_logs = getEveChatlogDir()
    app = QApplication(sys.argv)


    def enableShipParser(enable: bool = None) -> bool:
        ship_parser_change.emit(enable)
        if enable is not None:
            ship_parser_enabled = enable
        return ship_parser_enabled


    def enableCharacterParser(enable: bool = None) -> bool:
        char_parser_change.emit(enable)
        if enable is not None:
            character_parser_enabled = enable
        return character_parser_enabled


    def logFileChanged(path):
        t.addLogFile(path)


    # t = ChatThread(rooms, dotlan_systems=(), ship_parser_change, char_parser_change)

    EsiInterface(cache_dir=getVintelDir())
    dotlan = MyMap()
    dotlan.loadMap("Delve")

    t = ChatThread(rooms, dotlan_systems=dotlan.systems)
    t.start()
    filewatcherThread = FileWatcherThread(path_to_logs)
    filewatcherThread.file_change.connect(logFileChanged)
    filewatcherThread.start()
    app.exec_()
