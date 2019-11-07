#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
#

import six
import logging
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from vi.cache.cache import Cache

from vi.ui.ChatroomsChooser import Ui_Dialog
class ChatroomChooser(QtWidgets.QDialog, Ui_Dialog):
    rooms_changed = pyqtSignal(list)

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.defaultButton.clicked.connect(self.setDefaults)
        self.cancelButton.clicked.connect(self.accept)
        self.saveButton.clicked.connect(self.saveClicked)
        cache = Cache()
        roomnames = cache.getFromCache("room_names")
        if not roomnames:
            roomnames = u"querius.imperium,delve.imperium"
        self.roomnamesField.setPlainText(roomnames)


    def saveClicked(self):
        text = six.text_type(self.roomnamesField.toPlainText())
        rooms = [six.text_type(name.strip()) for name in text.split(",")]
        logging.debug("Added rooms: {}".format(rooms))
        self.accept()
        self.rooms_changed.emit(rooms)


    def setDefaults(self):
        self.roomnamesField.setPlainText(u"querius.imperium,delve.imperium")


