###########################################################################
#																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#																		  #
#																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import time
import logging
import sys

from six.moves import range
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QActionGroup, QMenu
from vi.resources import resourcePath
from vi import states
from ast import literal_eval
from vi.cache.cache import Cache
from vi.sound.soundmanager import SoundManager

LOGGER = logging.getLogger(__name__)


class TrayContextMenu(QtWidgets.QMenu):
    instances = set()

    def __init__(self, trayIcon=None):
        """ trayIcon = the object with the methods to call
        """
        QMenu.__init__(self)
        TrayContextMenu.instances.add(self)
        if trayIcon:
            self.trayIcon = trayIcon
        self._buildMenu()

    def _buildMenu(self):
        self.framelessCheck = QAction("Frameless Window", self)
        self.framelessCheck.setCheckable(True)
        self.framelessCheck.triggered.connect(self.trayIcon.changeFrameless)
        # self.connect(self.framelessCheck, PYQT_SIGNAL("triggered()"), self.trayIcon.changeFrameless)
        self.addAction(self.framelessCheck)
        self.addSeparator()
        self.requestCheck = QAction("Show status request notifications", self)
        self.requestCheck.setCheckable(True)
        self.requestCheck.setChecked(True)
        self.addAction(self.requestCheck)
        self.requestCheck.triggered.connect(self.trayIcon.switchRequest)
        # self.connect(self.requestCheck, PYQT_SIGNAL("triggered()"), self.trayIcon.switchRequest)
        self.alarmCheck = QAction("Show alarm notifications", self)
        self.alarmCheck.setCheckable(True)
        self.alarmCheck.setChecked(True)
        self.alarmCheck.triggered.connect(self.trayIcon.switchAlarm)
        # self.connect(self.alarmCheck, PYQT_SIGNAL("triggered()"), self.trayIcon.switchAlarm)
        self.addAction(self.alarmCheck)
        distanceMenu = self.addMenu("Alarm Distance")
        self.distanceGroup = QActionGroup(self)
        for i in range(0, 6):
            action = QAction("{0} Jumps".format(i), None)
            action.setCheckable(True)
            if i == 0:
                action.setChecked(True)
            action.alarmDistance = i
            action.triggered.connect(self.changeAlarmDistance)
            # self.connect(action, PYQT_SIGNAL("triggered()"), self.changeAlarmDistance)
            self.distanceGroup.addAction(action)
            distanceMenu.addAction(action)
        self.addMenu(distanceMenu)
        self.addSeparator()
        self.quitAction = QAction("Quit", self)
        self.quitAction.triggered.connect(self.trayIcon.quit)
        # self.connect(self.quitAction, PYQT_SIGNAL("triggered()"), self.trayIcon.quit)
        self.addAction(self.quitAction)
        f = getattr(sys, 'frozen', False)
        if not f:
            self.addSeparator()
            self.viewSource = QAction("View source", self)
            self.viewSource.triggered.connect(self.trayIcon.viewSource)
            self.addAction(self.viewSource)
            self.viewChats = QAction("View Chat-Logs", self)
            self.viewChats.triggered.connect(self.trayIcon.viewChatlogs)
            self.addAction(self.viewChats)


    def changeAlarmDistance(self):
        for action in self.distanceGroup.actions():
            if action.isChecked():
                self.trayIcon.alarmDistance = action.alarmDistance
                self.trayIcon.changeAlarmDistance()


class TrayIcon(QtWidgets.QSystemTrayIcon):
    # Min seconds between two notifications
    MIN_WAIT_NOTIFICATION = 15
    alarm_distance = pyqtSignal(int)
    change_frameless = pyqtSignal()
    quit_me = pyqtSignal()
    view_chatlogs = pyqtSignal()


    def __init__(self, app):
        self.resource_path = resourcePath()
        LOGGER.debug("TrayIcon looking for %s" % resourcePath("logo_small.png"))
        self.icon = QIcon(resourcePath("logo_small.png"))
        QSystemTrayIcon.__init__(self, self.icon, app)
        self.setToolTip("Your Vintel-Information-Service!")
        self.lastNotifications = {}
        self.setContextMenu(TrayContextMenu(self))
        self.showAlarm = True
        self.showRequest = True
        self.alarmDistance = 0

    def viewSource(self):
        pass

    def viewChatlogs(self):
        self.view_chatlogs.emit()

    def changeAlarmDistance(self):
        distance = self.alarmDistance
        self.alarm_distance.emit(distance)

    def changeFrameless(self):
        self.change_frameless.emit()

    @property
    def distanceGroup(self):
        return self.contextMenu().distanceGroup

    def quit(self):
        self.quit_me.emit()

    def switchAlarm(self):
        newValue = not self.showAlarm
        for cm in TrayContextMenu.instances:
            cm.alarmCheck.setChecked(newValue)
        self.showAlarm = newValue

    def switchRequest(self):
        newValue = not self.showRequest
        for cm in TrayContextMenu.instances:
            cm.requestCheck.setChecked(newValue)
        self.showRequest = newValue

    def showNotification(self, message, system, char, distance, soundlist: list = None):
        if message is None:
            return
        room = message.room
        title = None
        text = None
        icon = None
        text = ""
        soundFile = None
        orgSoundVolume = None
        if soundlist is None:
            try:
                soundlist = Cache().getFromCache("sound_setting_list")
                soundlist = literal_eval(soundlist)
            except Exception as e:
                LOGGER.error("Error while unpacking Cache", e)
                soundlist = None
        if soundlist:
            # set the sound which has been preconfigured
            orgSoundVolume = SoundManager().soundVolume
            if message.status == states.ALARM:
                row = soundlist[distance]
                SoundManager().setSoundVolume(row[2])
                soundFile = row[1]
            elif message.status == states.REQUEST:
                SoundManager().setSoundVolume(soundlist["Request"][2])
                soundFile = soundlist["Request"][1]
        if message.status == states.ALARM and self.showAlarm and self.lastNotifications.get(
                states.ALARM, 0) < time.time() - self.MIN_WAIT_NOTIFICATION:
            title = "ALARM!"
            icon = 2
            speechText = (
                u"{0} alarmed in {1}, {2} jumps from {3}".format(system, room, distance, char))
            text = (u"%s\n" % message.plainText) + speechText
            if soundFile:
                SoundManager().playSoundFile(soundFile, text, speechText)
                SoundManager().setSoundVolume(orgSoundVolume)
            else:
                SoundManager().playSound("alarm", text, speechText)
            self.lastNotifications[states.ALARM] = time.time()
        elif message.status == states.REQUEST and self.showRequest and self.lastNotifications.get(
                states.REQUEST, 0) < time.time() - self.MIN_WAIT_NOTIFICATION:
            title = "Status request"
            icon = 1
            text = u"Someone is requesting status of {0} in {1}.".format(system, room)
            self.lastNotifications[states.REQUEST] = time.time()
            if soundFile:
                SoundManager().playSoundFile(soundFile, text)
                SoundManager().setSoundVolume(orgSoundVolume)
            else:
                SoundManager().playSound("request", text)
        if not (title is None or text is None) or icon:
            if text == "":
                text = "{}".format(**locals())
            LOGGER.debug("Trayicon-Message: \"%s\"" % text)
            self.showMessage(title, text, icon)
