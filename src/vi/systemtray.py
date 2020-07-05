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
import time
import zroya
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QActionGroup, QMenu, QSystemTrayIcon

from vi.chat.chatmessage import Message
from vi.resources import resourcePath
from vi.settings.settings import SoundSettings, GeneralSettings
from vi.sound.soundmanager import SoundManager
from vi.states import State
import vi.version

class TrayIcon(QtWidgets.QSystemTrayIcon):
    # Min seconds between two notifications
    MIN_WAIT_NOTIFICATION = 15
    alarm_distance = pyqtSignal(int)
    change_frameless = pyqtSignal()
    quit_me = pyqtSignal()
    view_chatlogs = pyqtSignal()
    refresh_map = pyqtSignal()
    view_map_source = pyqtSignal()
    sound_active = pyqtSignal(bool)
    MAX_MESSAGES = 10

    def __init__(self, app):
        self.LOGGER = logging.getLogger(__name__)
        self.resource_path = resourcePath()
        self.LOGGER.debug("TrayIcon looking for %s", resourcePath("logo_small.png"))
        self.icon = QIcon(resourcePath("logo_small.png"))
        super().__init__(self.icon, app)
        self.setToolTip("Your Vintel-Information-Service!")
        self.lastNotifications = {}
        self.showAlarm = GeneralSettings().popup_notification
        self.showRequest = GeneralSettings().show_requests
        self.alarmDistance = GeneralSettings().alarm_distance
        self.soundActive = GeneralSettings().sound_active
        self._messages = []
        self.context_menu = TrayContextMenu(self)
        self.setContextMenu(self.context_menu)
        # zroya.init(vi.version.PROGNAME, vi.version.MAINTAINER, vi.version.PRODUCT_NAME, vi.version.SUB_PRODUCT, vi.version.VERSION)
        # self.notification = zroya.Template(zroya.TemplateType.ImageAndText1)

    def viewMapSource(self):
        self.view_map_source.emit()

    def refreshMap(self):
        self.refresh_map.emit()

    def viewChatLogs(self):
        self.view_chatlogs.emit()

    def changeAlarmDistance(self):
        self.alarm_distance.emit(self.alarmDistance)

    def changeFrameless(self):
        self.change_frameless.emit()

    def f_quit(self):
        self.quit_me.emit()

    def showMessage(
        self,
        title: str,
        msg: str,
        icon: "QSystemTrayIcon.MessageIcon" = QSystemTrayIcon.Information,
        msecs: int = 10000,
    ) -> None:
        # self.notification.setFirstLine(msg)
        # zroya.show(self.notification)
        super().showMessage(title, msg, icon, msecs)

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

    def switchSound(self):
        newValue = not self.soundActive
        for cm in TrayContextMenu.instances:
            cm.requestCheck.setChecked(newValue)
        self.soundActive = newValue
        GeneralSettings().sound_active = newValue
        self.sound_active.emit(newValue)

    def _get_sound(self, soundlist, status, distance) -> [str, int]:
        sound_setting_row = None
        if status == State["ALARM"]:
            sound_setting_row = soundlist[distance]
        elif status == State["REQUEST"]:
            for sub_list in soundlist:
                if "Request" in set(sub_list):
                    sound_setting_row = sub_list
        if sound_setting_row:
            sound_file = sound_setting_row[1]
            volume = sound_setting_row[2]
            return sound_file, volume
        self.LOGGER.error("No sound configured! %r", soundlist)
        return "", 0

    def showNotification(
        self,
        message: Message,
        system: str,
        char: str,
        distance: int,
        soundlist: list = None,
    ):
        if message is None:
            return
        room = message.room
        title = None
        text = None
        icon = QSystemTrayIcon.Information
        text = ""
        sound_file = None
        volume = None
        sound_setting_row = None
        if soundlist is None:
            soundlist = SoundSettings().sound
        # set the sound which has been preconfigured
        sound_file, volume = self._get_sound(soundlist, message.status, distance)
        if (
            message.status == State["ALARM"]
            and self.showAlarm
            and self.lastNotifications.get(State["ALARM"], 0)
            < time.time() - self.MIN_WAIT_NOTIFICATION
        ):
            title = "ALARM!"
            icon = QSystemTrayIcon.Warning
            speech_text = u"{0} alarmed in {1}, {2} jumps from {3}".format(
                system, room, distance, char
            )
            text = (u"%s\n" % message.plainText) + speech_text
            if sound_file:
                SoundManager().playSoundFile(sound_file, volume, text, speech_text)
            else:
                SoundManager().playSound("alarm", volume, text, speech_text)
            self.lastNotifications[State["ALARM"]] = time.time()
        elif (
            message.status == State["REQUEST"]
            and self.showRequest
            and self.lastNotifications.get(State["REQUEST"], 0)
            < time.time() - self.MIN_WAIT_NOTIFICATION
        ):
            title = "Status request"
            icon = QSystemTrayIcon.Information
            text = u"Someone is requesting status of {0} in {1}.".format(system, room)
            self.lastNotifications[State["REQUEST"]] = time.time()
            if sound_file:
                SoundManager().playSoundFile(sound_file, volume, text)
            else:
                SoundManager().playSound("request", volume, text)
        if title or text:
            # if not text or text == "":
            #     text = "{}".format(**locals())
            self.LOGGER.debug('Systemtray-Message: "%s": "%s"', title, text)
            self.showMessage(title, text, icon)


class TrayContextMenu(QtWidgets.QMenu):
    instances = set()

    def __init__(self, tray_icon: TrayIcon):
        """ trayIcon = the object with the methods to call
        """
        QMenu.__init__(self)
        TrayContextMenu.instances.add(self)
        self.trayIcon = tray_icon
        self.framelessCheck = QAction("Frameless Window", self)
        self.framelessCheck.setCheckable(True)
        self.framelessCheck.triggered.connect(self.trayIcon.changeFrameless)
        self.addAction(self.framelessCheck)
        self.addSeparator()
        self.requestCheck = QAction("Show status request notifications", self)
        self.requestCheck.setCheckable(True)
        self.requestCheck.setChecked(self.trayIcon.showRequest)
        self.addAction(self.requestCheck)
        self.requestCheck.triggered.connect(self.trayIcon.switchRequest)
        self.alarmCheck = QAction("Show alarm notifications", self)
        self.alarmCheck.setCheckable(True)
        self.alarmCheck.setChecked(self.trayIcon.showAlarm)
        self.alarmCheck.triggered.connect(self.trayIcon.switchAlarm)
        self.addAction(self.alarmCheck)
        distance_menu = self.addMenu("set Alarm Distance to ...")
        self.distanceGroup = QActionGroup(self)
        for distance in range(6):
            action = QAction("{0} Jumps".format(distance), None)
            action.setCheckable(True)
            if distance == self.trayIcon.alarmDistance:
                action.setChecked(True)
            action.alarmDistance = distance
            action.triggered.connect(self._change_alarm_distance)
            self.distanceGroup.addAction(action)
            distance_menu.addAction(action)
        self.addMenu(distance_menu)
        action = QAction("sound enabled", self)
        action.setCheckable(True)
        action.setChecked(self.trayIcon.soundActive)
        action.triggered.connect(self.trayIcon.switchSound)
        self.addAction(action)
        # are we in development mode
        if not getattr(sys, "frozen", False):
            self.addSeparator()
            debug_menu = self.addMenu("DEBUG ...")
            action = QAction("show monitored Chat-Logs", self)
            action.triggered.connect(self.trayIcon.viewChatLogs)
            debug_menu.addAction(action)
            action = QAction("view Map source", self)
            action.triggered.connect(self.trayIcon.viewMapSource)
            debug_menu.addAction(action)
            action = QAction("refresh Map", self)
            action.triggered.connect(self.trayIcon.refreshMap)
            debug_menu.addAction(action)
            self.addMenu(debug_menu)
        self.addSeparator()
        self.quitAction = QAction("Quit", self)
        self.quitAction.triggered.connect(self.trayIcon.f_quit)
        self.addAction(self.quitAction)

    def _change_alarm_distance(self):
        for action in self.distanceGroup.actions():
            if action.isChecked():
                self.trayIcon.alarmDistance = action.alarmDistance
                self.trayIcon.changeAlarmDistance()


if __name__ == "__main__":
    import sys
    import datetime
    from PyQt5.Qt import QApplication

    a = QApplication(sys.argv)
    d = TrayIcon(a)
    d.show()
    msg = Message("room", "message", datetime.datetime.now(), "Zedan")
    d.showNotification(msg, "Earth", "Zedan", 3)
    sys.exit(a.exec_())
