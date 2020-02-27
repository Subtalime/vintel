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
import threading
from vi.dotlan import mysystem as systems
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
from threading import Thread
from vi.chat.chatmessage import Message
from vi.chat.parser_functions import parseCharnames, parseShips, parseStatus, parseSystems, parseUrls
from vi import states

LOGGER = logging.getLogger(__name__)

__all_known_messages = {}

chat_thread_lock = threading.RLock()


def chat_search_key(message: Message):
    return message.plainText + message.user + message.room


def chat_thread_all_messages_contains(message: Message):
    """
    check if message is stored in the array
    only use vital information (ignore Timestamp)
    :param message:
    :return:
    """
    global __all_known_messages, chat_thread_lock
    chat_thread_lock.acquire()
    hit = False
    search = chat_search_key(message)
    if search in __all_known_messages.keys():
        diff = (__all_known_messages[search] - message.timestamp).total_seconds()
        if -1 <= diff <= 1:
            LOGGER.info("chat_message_contains: HIT Search \"{}\" (age {})".format(search, diff))
            hit = True
        else:
            LOGGER.info("chat_message_contains: NOT HIT Search \"{}\" (age {})".format(search, diff))
    chat_thread_lock.release()
    return hit


def _chat_thread_all_messages_tidy_up():
    global __all_known_messages
    # 20 minutes storage is enough
    # remember to adjust if increasing in ChatThreadProcess.__init__
    message_age = 1200
    ts = datetime.datetime.now()
    for key, mtime in list(__all_known_messages.items()):
        if (ts - mtime).total_seconds() > message_age:
            del __all_known_messages[key]


def chat_thread_all_messages_add(message: Message) -> bool:
    global __all_known_messages, chat_thread_lock
    chat_thread_lock.acquire()
    if chat_thread_all_messages_contains(message):
        chat_thread_lock.release()
        return False
    __all_known_messages[chat_search_key(message)] = message.timestamp
    _chat_thread_all_messages_tidy_up()
    chat_thread_lock.release()
    return True


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
    player_added_signal = pyqtSignal(list)
    message_added_signal = pyqtSignal(Message)
    message_updated_signal = pyqtSignal(Message)

    def __init__(self, parent, room_names: list, dotlan_systems: systems = {}, known_players: list = []):
        super(__class__, self).__init__()
        LOGGER.debug("Creating ChatThread")
        self.queue = Queue()
        self.active = True
        self.room_names = room_names
        self.dotlan_systems = dotlan_systems
        self.ship_parser = parent.enableShipParser()
        self.char_parser = parent.enableCharacterParser()
        parent.ship_parser.connect(self.ship_parser_enabled)
        parent.character_parser.connect(self.char_parser_enabled)
        self.process_pool = {}
        self.known_players = known_players

    # if file changed or file newly discovered
    def add_log_file(self, file_path: str, remove: bool = False):
        self.queue.put((file_path, remove))

    def remove_log_file(self, file_path: str):
        self.add_log_file(file_path, remove=True)

    def update_room_names(self, room_names: list):
        self.room_names = room_names
        self._tidy_logs()

    def add_character(self, player_name):
        if player_name not in self.known_players:
            self.known_players.append(player_name)
            self.player_added_signal.emit(self.known_players)

    def update_dotlan_systems(self, dotlan_systems: systems):
        LOGGER.debug("Informing Chat-Threads of new System")
        self.dotlan_systems = dotlan_systems
        for thread in self.process_pool.keys():
            self.process_pool[thread].update_dotlan_systems(self.dotlan_systems)

    def _tidy_logs(self):
        for path in self.process_pool.keys():
            room = os.path.basename(path)[:-20]
            if room not in self.room_names:
                self.add_log_file(path, True)

    def message_added(self, message: Message):
        if chat_thread_all_messages_add(message):
            self.message_added_signal.emit(message)

    def message_updated(self, message: Message):
        self.message_updated_signal.emit(message)

    def ship_parser_enabled(self, value):
        LOGGER.debug("Informing Chat-Threads of new Ship-Parser %r", value)
        self.ship_parser = value
        for thread in self.process_pool.keys():
            self.process_pool[thread].ship_parser_enabled(value)

    def char_parser_enabled(self, value):
        LOGGER.debug("Informing Chat-Threads of new Character-Parser %r", value)
        self.char_parser = value
        for thread in self.process_pool.keys():
            self.process_pool[thread].char_parser_enabled(value)

    def run(self):
        while self.active:
            logfile, delete = self.queue.get()
            if self.active:
                if logfile and logfile not in self.process_pool.keys() and not delete:
                    roomname = os.path.basename(logfile)[:-20]
                    if roomname not in self.room_names and roomname not in LOCAL_NAMES:
                        LOGGER.debug("Not interested in \"%s\" since not in monitored rooms", logfile)
                        continue
                    self.process_pool[logfile] = ChatThreadProcess(logfile, self.ship_parser, self.char_parser,
                                                                   self.dotlan_systems)
                    self.process_pool[logfile].message_added_s.connect(self.message_added)
                    self.process_pool[logfile].message_updated_s.connect(self.message_updated)
                    self.process_pool[logfile].new_player_s.connect(self.add_character)
                    self.process_pool[logfile].start()
                if delete and logfile in self.process_pool.keys():
                    self.process_pool[logfile].quit()
                    self.process_pool.pop(logfile)
                elif not delete:
                    self.process_pool[logfile].logfileChanged()

    def quit(self):
        for thread in self.process_pool.keys():
            LOGGER.debug("Closing Chat-Sub-Thread")
            self.process_pool[thread].quit()
        LOGGER.debug("Closing Main Chat-Thread")
        self.active = False
        self.add_log_file(None)
        QThread.quit(self)


class ChatThreadProcess(QThread):
    new_player_s = pyqtSignal(str)
    message_added_s = pyqtSignal(Message)
    message_updated_s = pyqtSignal(Message)

    def __init__(self, log_file_path: str, ship_scanner: bool, char_scanner: bool, dotlan_systems: systems = ()):
        super(__class__, self).__init__()
        self.queue = Queue()
        self.log_file = log_file_path
        self.ship_scanner = ship_scanner
        self.character_scanner = char_scanner
        self.dotlan_systems = dotlan_systems
        # any messages older than this will be ignored
        # this is if Vintal has started AFTER the EVE-Client started
        self.message_age = 300
        self.active = True
        self.charname = None
        self.roomname = None
        self.session_start = None
        self.parsed_lines = 0
        self.local_room = False
        self.knownMessages = []
        # locations of this character
        self.locations = []
        self.worker_loop = asyncio.new_event_loop()
        self.worker = Thread(target=self._runLoop)
        self.worker.start()

    def ship_parser_enabled(self, value: bool):
        self.ship_scanner = value

    def char_parser_enabled(self, value: bool):
        self.character_scanner = value

    def update_dotlan_systems(self, dotlan_systems: systems):
        self.dotlan_systems = dotlan_systems

    def _refineMessage(self, message: Message):
        LOGGER.debug("%s/%s: Start refining message: %r", self.roomname, self.charname, message)
        if self.ship_scanner:
            count = 0
            while parseShips(message.rtext):
                count += 1
                if count > 5:
                    LOGGER.warning("parseShips excessive runs on %r" % message.rtext)
                    break
                continue
        count = 0
        while parseUrls(message.rtext):
            count += 1
            if count > 5:
                LOGGER.warning("parseUrls excessive runs on %r" % message.rtext)
                break
            continue
        if self.character_scanner:
            count = 0
            while parseCharnames(message.rtext):
                count += 1
                if count > 5:
                    LOGGER.warning("parseCharnames excessive runs on %r" % message.rtext)
                    break
                continue

        # If message says clear and no system? Maybe an answer to a request?
        if message.status == states.CLEAR and not message.systems:
            maxSearch = 4  # we search only max_search messages in the room
            for count, oldMessage in enumerate(oldMessage for oldMessage in
                                               self.knownMessages[-1::-1]
                                               if oldMessage.room == self.roomname):
                if oldMessage.systems and oldMessage.status == states.REQUEST:
                    for system in oldMessage.systems:
                        message.systems.append(system)
                    break
                if count > maxSearch:
                    LOGGER.warning("parseOldMessages excessive runs on %r" % message.rtext)
                    break
        message.message = six.text_type(message.rtext)
        # multiple clients?
        self.knownMessages.append(message)
        if message.systems:
            for system in message.systems:
                system.messages.append(message)
        self.message_updated_s.emit(message)
        LOGGER.debug("%s/%s: Done refining message: %r", self.roomname, self.charname, message)

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
        self.new_player_s.emit(self.charname)
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
                    if chat_thread_all_messages_contains(message):
                        LOGGER.debug("%s/%s: Ignoring message (duplicate) from %s in %s", self.roomname, self.charname,
                                     message.user, message.room)
                        continue
                    # here, I believe, we should add it to the Widget-List and update
                    # the Map. Hence, we emit the Message
                    self.message_added_s.emit(message)
                    LOGGER.debug("%s/%s: Notify new message: %r", self.roomname, self.charname, message)
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
            LOGGER.debug("%s/%s: Message-Line too old", self.roomname, self.charname)
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
            LOGGER.debug("%s/%s: Message-Line too old", self.roomname, self.charname)
            return None
        # KOS request
        if upperText.startswith("XXX "):
            message = Message(self.roomname, text, timestamp, username, rtext=rtext,
                              status=states.KOS_STATUS_REQUEST, plainText=originalText, upperText=upperText)
        elif self.roomname.startswith("="):
            message = Message(self.roomname, "xxx " + text, timestamp, username,
                              status=states.KOS_STATUS_REQUEST, rtext=rtext, plainText=originalText,
                              upperText=upperText)
        elif upperText.startswith("VINTELSOUND_TEST"):
            message = Message(self.roomname, text, timestamp, username,
                              status=states.SOUND_TEST, rtext=rtext, plainText=originalText, upperText=upperText)
        else:
            parsedStatus = parseStatus(rtext)
            status = parsedStatus if parsedStatus is not None else states.ALARM
            message = Message(self.roomname, text, timestamp, username, status=status, rtext=rtext,
                              plainText=originalText, upperText=upperText)
            count = 0
            while parseSystems(self.dotlan_systems, message.rtext, message.systems):
                count += 1
                if count > 5:
                    LOGGER.error("parseSystems excessive runs on %r" % message.rtext)
                    break
                continue
        LOGGER.debug("%s/%s: Message created: %r", self.roomname, self.charname, message)
        return message

    def logfileChanged(self, val=1):
        self.queue.put(val)

    def run(self):
        while self.active:
            if self.active and not self.charname:
                # unusable log-file... end thread
                if not self._prepareParser():
                    self.active = False
                    return
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
    from vi.chat.filewatcherthread import FileWatcherThread
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
        t.add_log_file(path)


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
