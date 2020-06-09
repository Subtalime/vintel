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

import asyncio
import datetime
import logging
import os
import threading
from queue import Queue
from threading import Thread
from typing import Dict
import six
from PyQt5.QtCore import QThread, pyqtSignal
from vi.states import State
from vi.chat.messageparser import MessageParser, parse_line
from vi.chat.chatmessage import Message
from vi.dotlan import system as systems
from vi.settings.settings import GeneralSettings, ChatroomSettings
from vi.logger.mystopwatch import ViStopwatch

chat_thread_lock = threading.RLock()


__all_known_messages: Dict[str, datetime.datetime] = {}


def chat_search_key(message: Message):
    return "%s%s%s" % (message.plainText, message.user, message.room)


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
            logging.getLogger(__name__).debug(
                'chat_message_contains: duplicate found in search for "%s" (age %f)'
                % (search, diff,)
            )
            hit = True
    chat_thread_lock.release()
    return hit


def _chat_thread_all_messages_tidy_up():
    global __all_known_messages
    # 20 minutes storage is enough
    # remember to adjust if increasing in ChatThreadProcess.__init__
    message_age = 1200
    ts = datetime.datetime.now()
    for key, message_time in list(__all_known_messages.items()):
        if (ts - message_time).total_seconds() > message_age:
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


LOCAL_NAMES = (
    "Local",
    "Lokal",
    six.text_type("\u041B\u043E\u043A\u0430\u043B\u044C\u043D\u044B\u0439"),
)

"""
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
"""


class ChatThread(QThread):
    """
    Thread to react if the File-Watcher-Thread encounters any changes
    This will direct the change to the correct processing Thread-Queue
    """

    player_added_signal = pyqtSignal(list)
    message_added_signal = pyqtSignal(Message)
    message_updated_signal = pyqtSignal(Message)

    def __init__(
        self,
        # parent,
        # room_names: list,
        # ship_parser,
        # char_parser,
        dotlan_systems: systems = None,
        known_players: list = None,
    ):
        super(__class__, self).__init__()
        self.LOGGER = logging.getLogger(__name__)
        self.LOGGER.debug("Creating ChatThread")
        self.queue = Queue()
        self.active = True
        # self.room_names = room_names
        self.dotlan_systems = {}
        if dotlan_systems:
            self.dotlan_systems = dotlan_systems
        # self.ship_parser = ship_parser
        # self.char_parser = char_parser
        # self.ship_parser = parent.enableShipParser()
        # self.char_parser = parent.enableCharacterParser()
        # parent.ship_parser.connect(self.ship_parser_enabled)
        # parent.character_parser.connect(self.char_parser_enabled)
        self.process_pool = {}
        self.known_players = []
        if known_players:
            self.known_players = known_players

    @property
    def room_names(self):
        room_str = ChatroomSettings().room_names
        return room_str.split(",")

    # if file changed or file newly discovered
    def add_log_file(self, file_path: str, remove: bool = False):
        self.queue.put((file_path, remove))

    def remove_log_file(self, file_path: str):
        self.add_log_file(file_path, remove=True)

    def update_room_names(self, room_names: list):
        self.room_names = room_names
        self._tidy_logs()

    def add_known_player(self, player_name):
        if player_name not in self.known_players:
            self.known_players.append(player_name)
            self.player_added_signal.emit(self.known_players)

    def update_dotlan_systems(self, dotlan_systems: systems):
        self.LOGGER.debug("Informing Chat-Threads of new System")
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

    # def ship_parser_enabled(self, value):
    #     self.LOGGER.debug("Informing Chat-Threads of new Ship-Parser %r" % (value,))
    #     self.ship_parser = value
    #     for thread in self.process_pool.keys():
    #         self.process_pool[thread].ship_parser_enabled(value)
    #
    # def char_parser_enabled(self, value):
    #     self.LOGGER.debug(
    #         "Informing Chat-Threads of new Character-Parser %r" % (value,)
    #     )
    #     self.char_parser = value
    #     for thread in self.process_pool.keys():
    #         self.process_pool[thread].char_parser_enabled(value)
    #
    def run(self):
        while self.active:
            logfile, delete = self.queue.get()
            if self.active:
                if logfile and logfile not in self.process_pool.keys() and not delete:
                    roomname = os.path.basename(logfile)[:-20]
                    if roomname not in self.room_names and roomname not in LOCAL_NAMES:
                        self.LOGGER.debug(
                            'Not interested in "%s" since not in monitored rooms'
                            % (logfile,)
                        )
                        continue
                    # self.process_pool[logfile] = ChatThreadProcess(
                    #     logfile, self.ship_parser, self.char_parser, self.dotlan_systems
                    # )
                    self.process_pool[logfile] = ChatThreadProcess(
                        logfile, self.dotlan_systems
                    )
                    self.process_pool[logfile].message_added_s.connect(
                        self.message_added
                    )
                    self.process_pool[logfile].message_updated_s.connect(
                        self.message_updated
                    )
                    self.process_pool[logfile].new_player_s.connect(
                        self.add_known_player
                    )
                    self.process_pool[logfile].start()
                if delete and logfile in self.process_pool.keys():
                    self.process_pool[logfile].quit()
                    self.process_pool.pop(logfile)
                elif not delete:
                    self.process_pool[logfile].logfileChanged()

    def quit(self):
        for thread in self.process_pool.keys():
            self.LOGGER.debug("Closing Chat-Sub-Thread")
            self.process_pool[thread].quit()
        self.LOGGER.debug("Closing Main Chat-Thread")
        self.active = False
        self.add_log_file(None)
        QThread.quit(self)


class ChatThreadProcess(QThread):
    new_player_s = pyqtSignal(str)
    message_added_s = pyqtSignal(Message)
    message_updated_s = pyqtSignal(Message)

    def __init__(
        self,
        log_file_path: str,
        dotlan_systems: systems,
    ):
        super(__class__, self).__init__()
        self.LOGGER = logging.getLogger(__name__)
        self.queue = Queue()
        self.log_file = log_file_path
        # self.ship_scanner = ship_scanner
        # self.character_scanner = char_scanner
        self.dotlan_systems = dotlan_systems
        # any messages older than this will be ignored
        # this is if Vintal has started AFTER the EVE-Client started
        self.message_age = 300
        self.active = True
        self.charname = None
        self.roomname = None
        self.message_parser = None
        self.session_start = None
        self.parsed_lines = 0
        self.local_room = False
        self.knownMessages = []
        # locations of this character
        self.locations = {}
        self.worker_loop = asyncio.new_event_loop()
        self.worker = Thread(target=self._runLoop)
        self.worker.start()

    @property
    def ship_scanner(self):
        return GeneralSettings().ship_parser

    @property
    def character_scanner(self):
        return GeneralSettings().character_parser

    # def ship_parser_enabled(self, value: bool):
    #     self.ship_scanner = value
    #
    # def char_parser_enabled(self, value: bool):
    #     self.character_scanner = value
    #
    def update_dotlan_systems(self, dotlan_systems: systems):
        self.dotlan_systems = dotlan_systems
        # required to rescan all files, so map gets redrawn with current data
        self.charname = None

    def _refineMessage(self, message: Message):
        sw = ViStopwatch()
        with sw.timer("'{}'".format(message.plainText)):
            if self.ship_scanner:
                with sw.timer("Ship-Scanner"):
                    self.message_parser.process_ships(message)
            with sw.timer("Search URLs"):
                self.message_parser.process_urls(message)
            if self.character_scanner:
                with sw.timer("Scan character names"):
                    self.message_parser.process_charnames(message)

            # If message says clear and no system? Maybe an answer to a request?
            if message.status == State["CLEAR"] and not message.systems:
                max_search = 4  # we search only max_search messages in the room
                for count, oldMessage in enumerate(
                    oldMessage
                    for oldMessage in self.knownMessages[-1::-1]
                    if oldMessage.room == self.roomname
                ):
                    if oldMessage.systems and oldMessage.status == State["REQUEST"]:
                        for system in oldMessage.systems:
                            message.systems.append(system)
                        break
                    if count > max_search:
                        self.LOGGER.warning(
                            "parseOldMessages excessive runs on %r" % (message.rtext,)
                        )
                        break
            message.message = six.text_type(message.rtext)
            # multiple clients?
            self.knownMessages.append(message)
            with sw.timer("mark Systems"):
                if message.systems:
                    for system in message.systems:
                        system.messages.append(message)
            self.message_updated_s.emit(message)
        self.LOGGER.debug(sw.get_report())

    def _runLoop(self):
        asyncio.set_event_loop(self.worker_loop)
        self.worker_loop.run_forever()

    # get all the relevant information which ChatParser requires
    def _prepareParser(self) -> bool:
        self.LOGGER.debug("Analysing relevance of %s" % (self.log_file,))
        filename = os.path.basename(self.log_file)
        self.roomname = filename[:-20]
        if self.roomname in LOCAL_NAMES:
            self.local_room = True
        lines = self._getLines()
        # for local-chats we need more infos
        for line in lines:
            if "Listener:" in line:
                self.charname = line[line.find(":") + 1 :].strip()
            elif "Session started:" in line:
                session_str = line[line.find(":") + 1 :].strip()
                self.session_start = datetime.datetime.strptime(
                    session_str, "%Y.%m.%d %H:%M:%S"
                ).replace(tzinfo=datetime.timezone.utc)
            if self.charname and self.session_start:
                break
        if not self.charname or not self.session_start:
            self.LOGGER.warning(
                'File did not contain relevant information: "%s"' % (self.log_file,)
            )
            return False
        # tell the world we're monitoring a new character
        self.new_player_s.emit(self.charname)
        self.message_parser = MessageParser(
            self.roomname, self.charname, self.locations, self.local_room
        )
        # first 13 lines are Header information
        self.parsed_lines = 12
        # now head forward until you hit a timestamp, younger then max_age
        for line in lines[self.parsed_lines :]:
            if len(str(line).strip(" ")):
                utctime, username, text, timestamp = parse_line(line)
                if (
                    datetime.datetime.utcnow() - utctime
                ).total_seconds() <= self.message_age:
                    break
            self.parsed_lines += 1
        self.LOGGER.debug("Registered %s in %s" % (self.charname, self.roomname,))
        return True

    def _getLines(self) -> list:
        try:
            with open(self.log_file, "r", encoding="utf-16-le") as f:
                content = f.read()
            lines = content.split("\n")
        except Exception as e:
            self.LOGGER.error('Failed to read log file "%s" %r' % (self.log_file, e,))
            raise e
        return lines

    def _processFile(self):
        sw = ViStopwatch()
        with sw.timer("Process-File for '{}'".format(self.log_file)):
            lines = self._getLines()
            for line in lines[self.parsed_lines :]:
                line = line.strip()
                if len(line) > 2:
                    message = self.message_parser.process(line)
                    # if self.local_room:
                    #     message = self._parseLocal(line)
                    # else:
                    #     message = self._lineToMessage(line)
                    if message:
                        # multiple clients?
                        if chat_thread_all_messages_contains(message):
                            self.LOGGER.debug(
                                "%s/%s: Ignoring message (duplicate) from %s in %s"
                                % (
                                    self.roomname,
                                    self.charname,
                                    message.user,
                                    message.room,
                                )
                            )
                            continue
                        # here, I believe, we should add it to the Widget-List and update
                        # the Map. Hence, we emit the Message
                        # but ONLY after parsing the System-Status in the Message
                        self.message_parser.process_systems(self.dotlan_systems, message)
                        self.message_added_s.emit(message)
                        self.LOGGER.debug(
                            "%s/%s: Notify new message: %r"
                            % (self.roomname, self.charname, message,)
                        )
                        # Thereafter, the Worker-Loop can do the beautifying of the Widget
                        self.worker_loop.call_soon_threadsafe(self._refineMessage, message)
        self.LOGGER.debug(sw.get_report())
        self.parsed_lines = len(lines) - 1

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
        self.LOGGER.debug(
            "Closing Thread for %s in %s" % (self.charname, self.roomname,)
        )
        self.active = False
        self.logfileChanged(0)
        QThread.quit(self)


if __name__ == "__main__":
    from PyQt5.Qt import QApplication
    from vi.chat.filewatcherthread import FileWatcherThread
    from vi.resources import getEveChatlogDir, getVintelDir
    from vi.dotlan.mymap import MyMap
    from vi.esi import EsiInterface
    import sys

    logging.getLogger().setLevel(logging.DEBUG)

    rooms = "testbov"
    # rooms = ("delve.imperium", "querious.imperium", "testbov")
    path_to_logs = getEveChatlogDir()
    app = QApplication(sys.argv)

    def logFileChanged(path):
        t.add_log_file(path)

    # t = ChatThread(rooms, dotlan_systems=(), ship_parser_change, char_parser_change)

    EsiInterface(cache_dir=getVintelDir())
    dotlan = MyMap(region="Delve")

    t = ChatThread(dotlan_systems=dotlan.systems)
    t.start()
    filewatcherThread = FileWatcherThread(path_to_logs)
    filewatcherThread.file_change.connect(logFileChanged)
    filewatcherThread.start()
    app.exec_()
