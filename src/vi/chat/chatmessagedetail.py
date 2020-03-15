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
from PyQt5.QtCore import QThread, pyqtSignal
from .chatmessage import Message
from queue import Queue

LOGGER = logging.getLogger(__name__)


class ChatMessageDetail(QThread):
    message_updated = pyqtSignal(Message)

    def __init__(self):
        super(__class__, self).__init__()
        LOGGER.debug("Creating ChatThread")
        self.queue = Queue()
        self.active = True
