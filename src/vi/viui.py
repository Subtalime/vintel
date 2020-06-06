###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#
#
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import sys
import time
import six
import requests
import webbrowser
import vi.version
import logging

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QPoint, pyqtSignal, QPointF
from PyQt5.QtWidgets import (
    QMessageBox,
    QAction,
    QMainWindow,
    QStyleOption,
    QActionGroup,
    QStyle,
    QStylePainter,
    QSystemTrayIcon,
    QDialog,
)
from PyQt5.uic import loadUi
from vi.settings.settings import (
    GeneralSettings,
    ColorSettings,
    ChatroomSettings,
    RegionSettings,
)

# from vi import states
from vi.states import State
from vi.logger.logwindow import LogWindow
from vi.jumpbridge.Import import Import
from vi.cache.cache import Cache
from vi.resources import resourcePath
from vi.sound.soundmanager import SoundManager
from vi.threads import (
    AvatarFindThread,
    MapStatisticsThread,
    MapUpdateThread,
    ChatTidyThread,
)
from vi.systemtray import TrayContextMenu
from vi.chat.chatthread import ChatThread
from vi.chat.chatmessage import Message
from vi.chat.filewatcherthread import FileWatcherThread
from vi.esi import EsiInterface
from vi.esi.esihelper import EsiHelper
from vi.chat.chatentrywidget import ChatEntryWidget
from vi.jumpbridge.JumpbridgeDialog import JumpbridgeDialog
from vi.chat.systemchat import SystemChat
from vi.character.CharacterMenu import CharacterMenu, Characters
from vi.region.RegionMenu import RegionMenu
from vi.dotlan.regions import Regions
from vi.dotlan.mymap import MyMap
from vi.dotlan.exception import DotlanException
from vi.ui.MainWindow import Ui_MainWindow
from vi.logger.logconfig import LogConfigurationThread
from vi.settings.SettingsDialog import SettingsDialog
from vi.version import NotifyNewVersionThread
from vi.color.helpers import string_to_color
from vi.systemtray import TrayIcon
from vi.logger.mystopwatch import ViStopwatch
from vi.color.helpers import contrast_color, string_to_color


# Timer intervals
MESSAGE_EXPIRY_SECS = 20 * 60
MAP_UPDATE_INTERVAL_MSECS = 4 * 1000
CLIPBOARD_CHECK_INTERVAL_MSECS = 4 * 1000


class MainWindow(QMainWindow, Ui_MainWindow):
    chat_message_added = pyqtSignal(ChatEntryWidget)
    avatar_loaded = pyqtSignal(str, bytes)
    dotlan_systems = pyqtSignal(dict)
    character_parser = pyqtSignal(bool)
    ship_parser = pyqtSignal(bool)

    def __init__(self, path_to_logs: str, tray_icon: TrayIcon, background_color: str):
        super(self.__class__, self).__init__()
        self.sw = ViStopwatch()
        self.setupUi(self)
        # set the Splitter-Location
        self.splitter.setStretchFactor(8, 2)
        self.logWindow = LogWindow()

        self.LOGGER = logging.getLogger(__name__)
        # self.splitter.setSizes([1065, 839])
        self.avatarFindThread = None
        self.filewatcherThread = None
        self.chatTidyThread = None
        self.statisticsThread = None
        self.versionCheckThread = None
        self.mapUpdateThread = None
        self.logConfigThread = None
        self.selfNotify = False
        self.chatThread = None
        self.dotlan = None
        self.systems = None
        self.popup_notification = True
        self.character_parser_enabled = True
        self.ship_parser_enabled = True
        self.clipboard_check_interval = None
        self.backgroundColor = background_color
        self.cache = Cache()
        self.setWindowTitle(vi.version.DISPLAY)
        self.message_expiry = GeneralSettings().message_expiry
        self.setColor(GeneralSettings().background_color)
        # self.message_expiry = MESSAGE_EXPIRY_SECS
        self.clipboardCheckInterval()
        self.map_update_interval = GeneralSettings().map_update_interval
        self.setConstants()
        self.taskbarIconQuiescent = QtGui.QIcon(resourcePath("logo_small.png"))
        self.taskbarIconWorking = QtGui.QIcon(resourcePath("logo_small_green.png"))
        self.setWindowIcon(self.taskbarIconQuiescent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.pathToLogs = path_to_logs
        self.clipboardTimer = QtCore.QTimer(self)
        self.oldClipboardContent = ""
        self.trayIcon = tray_icon
        self.trayIcon.activated.connect(self.systemTrayActivated)
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.clipboard.clear(mode=self.clipboard.Clipboard)
        self.changeAlarmDistance(GeneralSettings().alarm_distance)
        self.initialMapPosition = None
        self.initialZoom = None
        self.lastStatisticsUpdate = 0
        self.chatEntries = []
        self.refreshContent = None
        self.frameButton.setVisible(False)
        self.scanIntelForKosRequestsEnabled = False
        self.mapPositionsDict = {}
        self.content = None
        # if LogConfiguration().LOG_FILE_PATH is None:
        #     self.LOGGER.warning("Logging is set to default. Please adjust {}".format(LogConfiguration().getLogFilePath()))
        # Load user's toon names
        self.knownPlayers = Characters()
        # here we are resetting our own menus, not the one from UI
        self.menubar.removeAction(self.menuCharacters.menuAction())
        self.menubar.removeAction(self.menuRegion.menuAction())
        self.menuCharacters = CharacterMenu("Characters", self)
        self.menubar.insertMenu(self.menuSound.menuAction(), self.menuCharacters)
        self.updateCharacterMenu()
        self.menuRegion = RegionMenu("Regions", self)
        self.menubar.insertMenu(self.menuSound.menuAction(), self.menuRegion)
        # Set up user's intel rooms
        roomnames = ChatroomSettings().room_names
        if roomnames:
            self.roomnames = roomnames.split(",")

        # Disable the sound UI if sound is not available
        if not SoundManager().soundAvailable:
            self.changeSound(disable=True)
        else:
            self.changeSound()

        # Set up Transparency menu - fill in opacity values and make connections
        self.opacityGroup = QActionGroup(self.menu)
        for i in (100, 80, 60, 40, 20):
            action = QAction("Opacity {0}%".format(i), None)
            action.setCheckable(True)
            if i == 100:
                action.setChecked(True)
            action.opacity = i / 100.0
            action.triggered.connect(self.changeOpacity)
            self.opacityGroup.addAction(action)
            self.menuTransparency.addAction(action)

        # Platform specific UI resizing - we size items in the resource files to look
        # correct on the mac, then resize other platforms as needed
        if sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
            font = self.statisticsButton.font()
            font.setPointSize(8)
            self.statisticsButton.setFont(font)
            self.jumpbridgesButton.setFont(font)
        elif sys.platform.startswith("linux"):
            pass

        self.wireUpUIConnections()
        self.recallCachedSettings()
        self.setupThreads()
        self.setupMap(True)

    def setColor(self, color: str = None) -> str:
        if color:
            self.backgroundColor = color
            color = string_to_color(self.backgroundColor)
            p = self.palette()
            p.setColor(self.backgroundRole(), color)
            self.setAutoFillBackground(True)
            self.setPalette(p)
            self.setStyleSheet(
                "QWidget { background-color: %s; color: %s; }"
                % (
                    self.backgroundColor,
                    contrast_color(string_to_color(self.backgroundColor)),
                )
            )

        return self.backgroundColor

    def setConstants(self):
        self.map_update_interval = GeneralSettings().map_update_interval
        if not self.map_update_interval:
            self.map_update_interval = MAP_UPDATE_INTERVAL_MSECS
            GeneralSettings().map_update_interval = self.map_update_interval
        self.clipboard_check_interval = GeneralSettings().clipboard_check_interval
        if not self.clipboard_check_interval:
            self.clipboard_check_interval = CLIPBOARD_CHECK_INTERVAL_MSECS
            GeneralSettings.clipboard_check_interval = self.clipboard_check_interval

    def updateCharacterMenu(self):
        try:
            self.menuCharacters.removeItems()
            self.LOGGER.debug(
                "Updating Character-Menu with Players: {}".format(self.knownPlayers)
            )
            self.menuCharacters.addItems(self.knownPlayers)
            self.menuCharacters.triggered.connect(self.char_menu_clicked)
        except Exception as e:
            self.LOGGER.error("updateCharacterMenu", e)

    def char_menu_clicked(self, action: "QAction"):
        self.LOGGER.debug(
            "Setting Character {} to Monitor {}".format(
                action.text(), action.isChecked()
            )
        )
        self.knownPlayers[action.text()].setMonitoring(action.isChecked())

    # TODO: unknown where is used (Window-Paint?)
    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QStylePainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

    def recallCachedSettings(self):
        try:
            self.cache.recall_and_apply_settings(self, "settings")
        except Exception as e:
            # TODO: add a button to delete the cache / DB
            self.cache.put("settings", "", 0)
            msg = "Something went wrong loading saved state:\n {0}".format(str(e))
            self.LOGGER.error(msg)
            self.trayIcon.showMessage("Settings error", msg)

    def wireUpUIConnections(self):
        # Wire up general UI connections
        # KOS disabled, since it's only working for CVA
        self.kosClipboardActiveAction.setEnabled(False)
        self.autoScanIntelAction.setEnabled(False)

        self.clipboard.changed.connect(self.clipboardChanged)
        self.autoScanIntelAction.triggered.connect(self.changeAutoScanIntel)
        self.kosClipboardActiveAction.triggered.connect(self.changeKosCheckClipboard)
        self.zoomInButton.clicked.connect(self.zoomMapIn)
        self.zoomOutButton.clicked.connect(self.zoomMapOut)
        self.statisticsButton.clicked.connect(self.changeStatisticsVisibility)
        self.jumpbridgesButton.clicked.connect(self.changeJumpbridgesVisibility)
        self.chatLargeButton.clicked.connect(self.chatLarger)
        self.chatSmallButton.clicked.connect(self.chatSmaller)
        self.actionAbout.triggered.connect(self.showInfo)
        self.showChatAvatarsAction.triggered.connect(self.changeShowAvatars)
        self.alwaysOnTopAction.triggered.connect(self.changeAlwaysOnTop)
        self.chooseChatRoomsAction.triggered.connect(self.showChatroomChooser)

        self.showChatAction.triggered.connect(self.changeChatVisibility)
        self.soundSetupAction.triggered.connect(self.showSoundSetup)
        self.activateSoundAction.triggered.connect(self.trayIcon.sound_active)
        self.useSpokenNotificationsAction.triggered.connect(
            self.changeUseSpokenNotifications
        )
        self.trayIcon.alarm_distance.connect(self.changeAlarmDistance)
        self.framelessWindowAction.triggered.connect(self.changeFrameless)
        self.trayIcon.change_frameless.connect(self.changeFrameless)
        self.trayIcon.view_chatlogs.connect(self.viewChatlogs)
        self.trayIcon.refresh_map.connect(self.updateMapView)
        self.frameButton.clicked.connect(self.changeFrameless)
        self.actionQuit.triggered.connect(self.close)
        self.trayIcon.quit_me.connect(self.close)
        self.menuRegion.triggered[QAction].connect(self.processRegionSelectMenu)
        self.mapView.page().scroll_detected.connect(self.mapPositionChanged)
        self.actionSettings.triggered.connect(self.settings)
        self.actionSettings.setEnabled(True)

        # if Log-Window is disabled for any reason
        if not self.logWindow:
            self.actionLogging.setEnabled(False)
        self.actionLogging.triggered.connect(self.showLoggingWindow)

    def viewChatlogs(self):
        logs = ""
        for log in self.chatThread.process_pool.keys():
            logs += "{}\r\n".format(log)
        QMessageBox.information(None, "Monitored logs", "%s" % logs, QMessageBox.Ok)

    def settings(self, tabIndex: int = 0):
        def handleRegionsChosen(regionList):
            self.LOGGER.debug("Chosen new Regions to monitor")
            self.menuRegion.addItems()

        setting = SettingsDialog(self, tabIndex)
        # setting.new_region_range_chosen.connect(handleRegionsChosen)
        # setting.rooms_changed.connect(self.changedRoomnames)
        # setting.checkScanCharacter.setChecked(self.character_parser_enabled)
        # setting.checkShipNames.setChecked(self.ship_parser_enabled)
        # setting.txtKosInterval.setText(str(int(self.clipboard_check_interval / 1000)))
        # setting.txtMessageExpiry.setText(str(self.messageExpiry()))
        # setting.checkNotifyOwn.setChecked(self.selfNotify)
        # setting.checkPopupNotification.setChecked(self.popup_notification)
        # setting.color = self.setColor()
        # setting.tabWidget.setCurrentIndex(tabIndex)
        # setting.txtJumpDistance.setText(str(self.alarmDistance))

        setting.show()
        # return True if Changes have been applied
        if setting.exec_():
            # self.setColor(GeneralSettings().background_color)
            self.enableCharacterParser(GeneralSettings().character_parser)
            self.enableShipParser(GeneralSettings().ship_parser)
            self.enablePopupNotification(GeneralSettings().popup_notification)
            self.clipboardCheckInterval(GeneralSettings().clipboard_check_interval)
            self.messageExpiry(GeneralSettings().message_expiry)
            self.enableSelfNotify(GeneralSettings().self_notify)
            self.changeAlarmDistance(GeneralSettings().alarm_distance)

    def enableSelfNotify(self, enable: bool = None) -> bool:
        if enable is not None:
            self.selfNotify = enable
        return self.selfNotify

    def enablePopupNotification(self, enable: bool = None) -> bool:
        if enable is not None:
            self.popup_notification = enable
        return self.popup_notification

    def clipboardCheckInterval(self, value: int = None):
        if value:
            self.clipboard_check_interval = GeneralSettings().clipboard_check_interval
        if self.clipboard_check_interval is None:
            self.clipboard_check_interval = GeneralSettings().clipboard_check_interval

        return self.clipboard_check_interval

    # Menu-Selection of Regions
    def processRegionSelectMenu(self, qAction: "QAction"):
        if qAction.objectName() == "region_select":
            self.LOGGER.debug("Opened Region-Selector Dialog")
            self.showRegionChooser()
        elif qAction.objectName() == "jumpbridge_select":
            self.LOGGER.debug("Opened JumpBridge dialog")
            self.showJumpBridgeChooser()
        else:
            RegionSettings().selected_region = qAction.text()
            self.LOGGER.debug("Set Region to {}".format(qAction.text()))
            self.setupMap()

    # Dialog to select Regions to monitor
    def showRegionChooser(self):
        self.settings(3)
        # def handleRegionsChosen(regionList):
        #     LOGGER.debug("Chosen new Regions to monitor")
        #     self.menuRegion.addItems()
        #
        # chooser = RegionChooserList(self)
        # chooser.new_region_range_chosen.connect(handleRegionsChosen)
        # chooser.show()

    def updatePlayers(self, player_list: list):
        self.knownPlayers.addNames(player_list)
        self.updateCharacterMenu()

    def setupThreads(self):
        self.LOGGER.debug("Creating threads")

        self.logConfigThread = LogConfigurationThread(self.logWindow)
        self.logConfigThread.start()

        self.versionCheckThread = NotifyNewVersionThread()
        self.versionCheckThread.newer_version.connect(self.notifyNewerVersion)
        self.versionCheckThread.start()
        # TODO: make sure this has completed loading before starting any other
        # threads. i.e. the Chat-Message threads try to highlight the Map, but since
        # it hasn't yet loaded, it can't mark them
        self.mapUpdateThread = MapUpdateThread()
        self.mapUpdateThread.map_update.connect(self.mapUpdate)
        self.mapUpdateThread.start()

        # Set up threads and their connections
        self.avatarFindThread = AvatarFindThread()
        self.avatarFindThread.avatar_update.connect(self.updateAvatarOnChatEntry)
        self.avatarFindThread.start()

        # self.kosRequestThread = KOSCheckerThread()
        # self.kosRequestThread.kos_result.connect(self.showKosResult)
        # self.kosRequestThread.start()

        self.chatThread = ChatThread()
        # self.chatThread = ChatThread(room_names=self.roomnames, ship_parser=self.enableShipParser(), char_parser=self.enableCharacterParser())
        self.chatThread.message_added_signal.connect(self.logFileChanged)
        self.chatThread.message_updated_signal.connect(
            self.updateMessageDetailsOnChatEntry
        )
        self.chatThread.player_added_signal.connect(self.updatePlayers)
        self.chatThread.start()

        self.filewatcherThread = FileWatcherThread(self.pathToLogs)
        self.filewatcherThread.file_change.connect(self.chatThread.add_log_file)
        self.filewatcherThread.file_removed.connect(self.chatThread.remove_log_file)
        self.filewatcherThread.start()

        self.chatTidyThread = ChatTidyThread(self.message_expiry)
        self.chatTidyThread.time_up.connect(self.pruneMessages)
        self.chatTidyThread.start()

        self.statisticsThread = MapStatisticsThread()
        self.statisticsThread.statistic_data_update.connect(self.updateStatisticsOnMap)
        # statisticsThread is blocked until first call of requestStatistics
        self.statisticsThread.start()

        self.LOGGER.debug("Finished Creating threads")

    # TODO: store each system configured in Regions
    # TODO: therefore if we switch Region, we can update with previously found data
    # TODO: when clicking on System in Chat, scroll to the position within the Map
    def setupMap(self, initialize=False):
        if self.filewatcherThread:
            self.filewatcherThread.paused = True
        if self.mapUpdateThread:
            self.mapUpdateThread.pause(True)
        self.LOGGER.debug("Finding map file")
        regionName = RegionSettings().selected_region
        if not regionName:
            regionName = "Delve"

        try:
            self.dotlan = MyMap(parent=self, region=regionName)
        except DotlanException as e:
            self.LOGGER.error(e)
            QMessageBox.critical(None, "Error getting map", six.text_type(e))
            # Workaround for invalid Cache-Content
            if regionName != "Delve":
                regionName = RegionSettings().selected_region = "Delve"
                self.dotlan = MyMap(parent=self, region=regionName)
            else:
                sys.exit(1)
        self.LOGGER.debug("Map File found, Region set to {}".format(regionName))

        # Load the jumpbridges
        with self.sw.timer("setJumpbridges"):
            self.setJumpbridges()
        self.LOGGER.debug(self.sw.get_report())
        self.systems = self.dotlan.systems
        self.dotlan_systems.emit(self.systems)
        if self.chatThread:
            self.chatThread.update_dotlan_systems(self.systems)

        # Menus - only once
        if initialize:
            self.LOGGER.debug("Initializing contextual menus")

            # Add a contextual menu to the mapView
            def mapContextMenuEvent(event):
                # if QApplication.activeWindow() or QApplication.focusWidget():
                self.mapView.view.contextMenu.exec_(
                    self.mapToGlobal(QPoint(event.x(), event.y()))
                )

            # TODO: this stopped working after changing PanningWebView to QWidget
            self.mapView.view.contextMenuEvent = mapContextMenuEvent
            self.mapView.view.contextMenu = self.trayIcon.contextMenu()

            # Clicking links
            self.statisticsButton.setCheckable(True)
            self.statisticsButton.setChecked(False)
            self.mapView.page().link_clicked.connect(self.mapLinkClicked)
            self.LOGGER.debug("DONE Initializing contextual menus")

            # update Character-Locations
            for char in self.knownPlayers:
                if self.knownPlayers[char].getLocation():
                    self.set_player_location(
                        char, self.knownPlayers[char].getLocation(), False
                    )
            # self.restartMapTimer()

        if self.mapUpdateThread:
            self.mapUpdateThread.pause(False)
        self.setInitialMapPositionForRegion(regionName)
        self.checkJumpbridges()
        self.updateMapView()
        self.refreshContent = self.dotlan.svg
        self.setInitialMapPositionForRegion(regionName)
        # here is a good spot to update the Map with current Chat-Entries

        # Allow the file watcher to run now that all else is set up
        if self.filewatcherThread:
            self.filewatcherThread.paused = False
        self.LOGGER.debug("Map setup complete")

    def startClipboardTimer(self):
        """
            Start a timer to check the keyboard for changes and kos check them,
            first initializing the content so we dont kos check from random content
        """
        self.oldClipboardContent = tuple(six.text_type(self.clipboard.text()))
        self.clipboardTimer.timeout.connect(self.clipboardChanged)
        self.clipboardTimer.start(self.clipboard_check_interval)

    def stopClipboardTimer(self):
        if self.clipboardTimer:
            try:
                self.clipboardTimer.timeout.disconnect(self.clipboardChanged)
            except:
                pass
            self.clipboardTimer.stop()

    def restartClipboardTimer(self):
        self.stopClipboardTimer()
        self.startClipboardTimer()

    def closeEvent(self, event):
        """
            Persisting things to the cache before closing the window
        """
        # Known playernames
        self.knownPlayers.storeData()
        # Program state to cache (to read it on next startup)
        settings = (
            (None, "restoreGeometry", bytes(self.saveGeometry())),
            (None, "restoreState", bytes(self.saveState())),
            ("splitter", "restoreGeometry", bytes(self.splitter.saveGeometry())),
            ("splitter", "restoreState", bytes(self.splitter.saveState())),
            ("mapView", "setZoomFactor", self.mapView.page().zoomFactor()),
            (None, "changeChatFontSize", ChatEntryWidget.TEXT_SIZE),
            (None, "changeOpacity", self.opacityGroup.checkedAction().opacity),
            (None, "changeAlwaysOnTop", self.alwaysOnTopAction.isChecked()),
            (None, "changeShowAvatars", self.showChatAvatarsAction.isChecked()),
            # (None, "changeAlarmDistance", self.alarmDistance),
            # (None, "enableCharacterParser", self.character_parser_enabled),
            # (None, "enableShipParser", self.ship_parser_enabled),
            # (None, "enableSelfNotify", self.selfNotify),
            # (None, "enablePopupNotification", self.popup_notification),
            # (None, "messageExpiry", self.message_expiry),
            (None, "changeSound", self.activateSoundAction.isChecked()),
            (None, "changeChatVisibility", self.showChatAction.isChecked()),
            (None, "loadInitialMapPositions", self.mapPositionsDict),
            (None, "setColor", self.backgroundColor),
            (None, "changeFrameless", self.framelessWindowAction.isChecked()),
            (
                None,
                "changeUseSpokenNotifications",
                self.useSpokenNotificationsAction.isChecked(),
            ),
            (
                None,
                "changeKosCheckClipboard",
                self.kosClipboardActiveAction.isChecked(),
            ),
            (None, "changeAutoScanIntel", self.scanIntelForKosRequestsEnabled),
        )
        try:
            self.cache.save_settings("settings", settings, 60 * 60 * 24 * 30)
        except Exception:
            pass
        # strsettings = str(settings)
        # self.cache.put("settings", strsettings, 60 * 60 * 24 * 30)

        # Stop the threads
        try:
            SoundManager().quit()
            if self.logConfigThread:
                self.logConfigThread.quit()
            if self.chatThread:
                self.chatThread.quit()
            if self.avatarFindThread:
                self.avatarFindThread.quit()
            if self.chatTidyThread:
                self.chatTidyThread.quit()
            if self.filewatcherThread:
                self.filewatcherThread.quit()
            # self.kosRequestThread.quit()
            # self.kosRequestThread.wait()
            if self.versionCheckThread:
                self.versionCheckThread.quit()
            if self.statisticsThread:
                self.statisticsThread.quit()
            if self.mapUpdateThread:
                self.mapUpdateThread.quit()
        except Exception as e:
            self.LOGGER.exception("Error while stopping a Thread", e)
        self.trayIcon.hide()
        if self.logWindow:
            self.logWindow.close()
        # sys.exit(0)

    def notifyNewerVersion(self, newestVersion):
        msg = (
            "An update is available for {}. Current V{} to V{}\n"
            "Consider upgrading by visiting {}".format(
                vi.version.PROGNAME, vi.version.VERSION, newestVersion, vi.version.URL
            )
        )
        self.LOGGER.warning(msg)
        self.trayIcon.showMessage("Newer Version", msg)

    def changeChatVisibility(self, newValue=None):
        if newValue is None:
            newValue = self.showChatAction.isChecked()
        self.showChatAction.setChecked(newValue)
        self.chatbox.setVisible(newValue)

    def changeKosCheckClipboard(self, newValue=None):
        if newValue is None:
            newValue = self.kosClipboardActiveAction.isChecked()
        self.kosClipboardActiveAction.setChecked(newValue)
        if newValue:
            self.startClipboardTimer()
        else:
            self.stopClipboardTimer()

    def changeAutoScanIntel(self, newValue=None):
        if newValue is None:
            newValue = self.autoScanIntelAction.isChecked()
        self.autoScanIntelAction.setChecked(newValue)
        self.scanIntelForKosRequestsEnabled = newValue

    def changeUseSpokenNotifications(self, newValue=None):
        if SoundManager().platformSupportsSpeech():
            if newValue is None:
                newValue = self.useSpokenNotificationsAction.isChecked()
            self.useSpokenNotificationsAction.setChecked(newValue)
            SoundManager().setUseSpokenNotifications(newValue)
        else:
            self.useSpokenNotificationsAction.setChecked(False)
            self.useSpokenNotificationsAction.setEnabled(False)

    def changeOpacity(self, newValue=None):
        try:
            action = self.opacityGroup.checkedAction()
            newValue = action.opacity
            if newValue is not None:
                for action in self.opacityGroup.actions():
                    if action.opacity == newValue:
                        action.setChecked(True)
                        break
            self.setWindowOpacity(action.opacity)
        except Exception as e:
            self.LOGGER.error("Error while selecting Opacity", e)

    def changeSound(self, newValue=None, disable=False):
        if disable:
            self.activateSoundAction.setChecked(False)
            self.activateSoundAction.setEnabled(False)
            self.soundSetupAction.setEnabled(False)
            # self.soundButton.setEnabled(False)
            QMessageBox.warning(
                None,
                "Sound disabled",
                "The lib 'pyglet' which is used to play sounds cannot "
                "be found, so the soundsystem is disabled.\nIf you want sound, "
                "please install the 'pyglet' library. This warning will "
                "not be shown again.",
                QMessageBox.Ok,
            )
        else:
            self.soundSetupAction.setEnabled(True)
            if newValue is None:
                newValue = GeneralSettings().sound_active
            self.activateSoundAction.setChecked(newValue)
            self.soundSetupAction.setEnabled(newValue)
            # SoundManager().enable_sound = newValue
            GeneralSettings().sound_active = newValue
            self.LOGGER.info("Sound activation changed to %r", newValue)

    def changeAlwaysOnTop(self, newValue=None):
        if newValue is None:
            newValue = self.alwaysOnTopAction.isChecked()
        self.hide()
        self.alwaysOnTopAction.setChecked(newValue)
        if newValue:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & (~QtCore.Qt.WindowStaysOnTopHint))
        self.show()

    def changeFrameless(self, newValue=None):
        if newValue is None:
            newValue = not self.frameButton.isVisible()
        self.hide()
        if newValue:
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            self.changeAlwaysOnTop(True)
        else:
            self.setWindowFlags(self.windowFlags() & (~QtCore.Qt.FramelessWindowHint))
        self.menubar.setVisible(not newValue)
        self.frameButton.setVisible(newValue)
        self.framelessWindowAction.setChecked(newValue)

        for cm in TrayContextMenu.instances:
            cm.framelessCheck.setChecked(newValue)
        self.show()

    def changeShowAvatars(self, newValue=None):
        if newValue is None:
            newValue = self.showChatAvatarsAction.isChecked()
        self.showChatAvatarsAction.setChecked(newValue)
        ChatEntryWidget.SHOW_AVATAR = newValue
        for entry in self.chatEntries:
            entry.avatarLabel.setVisible(newValue)

    def changeChatFontSize(self, newSize):
        if newSize:
            for entry in self.chatEntries:
                entry.changeFontSize(newSize)
            ChatEntryWidget.TEXT_SIZE = newSize

    def chatSmaller(self):
        newSize = ChatEntryWidget.TEXT_SIZE - 1
        self.changeChatFontSize(newSize)

    def chatLarger(self):
        newSize = ChatEntryWidget.TEXT_SIZE + 1
        self.changeChatFontSize(newSize)

    def messageExpiry(self, seconds: int = None) -> int:
        if seconds:
            self.message_expiry = int(seconds)
        self.chatbox.setTitle(
            "All intel (past {} minutes)".format(int(self.message_expiry) / 60)
        )
        return self.message_expiry

    def enableCharacterParser(self, enable: bool = None) -> bool:
        if enable is not None:
            self.character_parser_enabled = enable
            self.character_parser.emit(enable)
        return self.character_parser_enabled

    def enableShipParser(self, enable: bool = None) -> bool:
        if enable is not None:
            self.ship_parser_enabled = enable
            self.ship_parser.emit(enable)
        return self.ship_parser_enabled

    def changeAlarmDistance(self, distance: int):
        self.alarmDistance = int(distance)
        for cm in TrayContextMenu.instances:
            for action in cm.distanceGroup.actions():
                if action.alarmDistance == distance:
                    action.setChecked(True)
        self.trayIcon.alarmDistance = int(distance)

    def changeJumpbridgesVisibility(self):
        newValue = self.dotlan.changeJumpbridgesVisibility()
        self.jumpbridgesButton.setChecked(newValue)
        self.updateMapView()

    def changeStatisticsVisibility(self):
        newValue = self.dotlan.changeStatisticsVisibility()
        self.statisticsButton.setChecked(newValue)
        self.updateMapView()
        if newValue:
            self.statisticsThread.requestStatistics()

    def clipboardChanged(self, mode=0):
        if not (
            mode == 0
            and self.kosClipboardActiveAction.isChecked()
            and self.clipboard.mimeData().hasText()
        ):
            return
        content = six.text_type(self.clipboard.text())
        contentTuple = tuple(content)
        # Limit redundant kos checks
        if contentTuple != self.oldClipboardContent:
            parts = tuple(content.split("\n"))
            for part in parts:
                # Make sure user is in the content (this is a check of the local system in Eve).
                # also, special case for when you have no knonwnPlayers (initial use)
                if not self.knownPlayers or part in self.knownPlayers:
                    self.trayIcon.setIcon(self.taskbarIconWorking)
                    self.kosRequestThread.addRequest(parts, "clipboard", True)
                    break
            self.oldClipboardContent = contentTuple

    # emitted by MapView
    def mapLinkClicked(self, url):
        systemName = six.text_type(url.path().split("/")[-1]).upper()
        try:
            system = self.systems[str(systemName)]
            sc = SystemChat(
                self, SystemChat.SYSTEM, system, self.chatEntries, self.knownPlayers
            )
            self.chat_message_added.connect(sc.addChatEntry)
            self.avatar_loaded.connect(sc.newAvatarAvailable)
            sc.location_set.connect(self.set_player_location)
            sc.show()
        except Exception as e:
            self.LOGGER.error('mapLinkClicked problem for "%s": %r', systemName, e)
            pass

    def markSystemOnMap(self, systemname):
        self.systems[six.text_type(systemname)].mark()
        # if this function is called from the Chat-Entry-Widget Click emitter
        # perhaps here, a Scroll-To the coordinates stored in self.systems[system-name]
        zoomfactor = float(self.mapView.page().zoomFactor())
        self.scrollTo(
            self.systems[six.text_type(systemname)].mapCoordinates["center_x"]
            / zoomfactor,
            self.systems[six.text_type(systemname)].mapCoordinates["center_y"]
            / zoomfactor,
        )
        self.updateMapView()

    def set_player_location(self, player_name, new_system, update_view: bool = True):
        for system in self.systems.values():
            system.removeLocatedCharacter(player_name)
        if not new_system == "?" and new_system in self.systems:
            self.systems[new_system].addLocatedCharacter(player_name)
            self.knownPlayers[player_name].setLocation(new_system)
        # character location highlight update
        if update_view:
            self.updateMapView()

    def scrollTo(self, x, y):
        _scrollTo = str(
            "window.scrollTo({}, {});".format(
                x / self.mapView.page().zoomFactor(),
                y / self.mapView.page().zoomFactor(),
            )
        )
        # self.mapView.page().runJavaScript(_scrollTo)
        self.initialMapPosition = QPointF(x, y)

    def mapUpdate(self, newContent=None):
        if newContent:
            self.refreshContent = newContent  # triggered by mapUpdateThread
        if self.refreshContent:
            self.mapView.setHtml(self.refreshContent)

    def updateStatisticsOnMap(self, data):
        if not self.statisticsButton.isChecked():
            return
        self.LOGGER.debug("Updating statistics on Map")
        if data["result"] == "ok":
            self.dotlan.addSystemStatistics(data["statistics"])
        elif data["result"] == "error":
            text = data["text"]
            self.trayIcon.showMessage("Loading statstics failed", text)
            self.LOGGER.error("updateStatisticsOnMap, error: %s" % text)

    def inject(self, on):
        if on:
            alarm = "'request'"
        else:
            alarm = "'clear'"
        script = (
            "showTimer(0, {}, "
            "document.querySelector('#txt30004726'), "
            "document.querySelector('#rect30004726'), "
            "document.querySelector('#rect30004726'));".format(alarm)
        )
        self.mapView.page().runJavaScript(script)

    def updateMapView(self):
        scrollPosition = self.mapView.page().scrollPosition()
        zoom = self.mapView.page().zoomFactor()
        if self.initialMapPosition:
            scrollPosition = self.initialMapPosition
            zoom = self.initialZoom
            self.initialMapPosition = self.initialZoom = None
        self.dotlan.mapUpdate(zoom, scrollPosition)
        self.mapUpdateThread.queue.put((self.dotlan.svg, zoom, scrollPosition))

    def zoomMapIn(self):
        self.mapView.setZoomFactor(self.mapView.zoomFactor + 0.1)
        # self.inject(True)

    def zoomMapOut(self):
        self.mapView.setZoomFactor(self.mapView.zoomFactor - 0.1)
        # self.inject(False)

    def loadInitialMapPositions(self, newDictionary):
        self.mapPositionsDict = newDictionary

    def setInitialMapPositionForRegion(self, regionName):
        try:
            if not regionName:
                regionName = self.cache.fetch("region_name")
            if regionName:
                xy, zoom = self.mapPositionsDict[regionName]
                self.initialMapPosition = QPoint(xy[0], xy[1])
                self.initialZoom = zoom
        except:
            pass

    def mapPositionChanged(self, qPointF):
        """store the current Scroll-Position for current Region.
        if we change Regions, it allows us to jump back to the stored position
        :param qPointF:
        :return:
        """
        regionName = RegionSettings().selected_region
        if regionName:
            scrollPosition = self.mapView.page().scrollPosition()
            self.mapPositionsDict[regionName] = (
                (scrollPosition.x(), scrollPosition.y()),
                self.mapView.page().zoomFactor(),
            )

    def showLoggingWindow(self):
        if self.logWindow.isHidden():
            self.logWindow.showNormal()
            self.logWindow.activateWindow()

    def showChatroomChooser(self):
        self.settings(4)

    def showJumpBridgeChooser(self):
        chooser = JumpbridgeDialog(self)
        chooser.set_jump_bridge_url.connect(self.setJumpbridges)
        chooser.exec_()

    # TODO: new settings
    def checkJumpbridges(self):
        data = self.cache.fetch_jumpbridge_data()
        if data:
            self.jumpbridgesButton.setEnabled(True)
            self.jumpbridgesButton.setCheckable(True)
            self.jumpbridgesButton.setChecked(False)
        else:
            self.jumpbridgesButton.setEnabled(False)
            self.jumpbridgesButton.setCheckable(False)
            self.jumpbridgesButton.setChecked(False)

    # TODO: new settings
    def setJumpbridges(self, url_or_filepath: str = None, clipdata: str = None):
        data = []
        try:
            if url_or_filepath:
                if url_or_filepath.startswith("http"):
                    try:
                        resp = requests.get(url_or_filepath)
                        for line in resp.iter_lines(decode_unicode=True):
                            parts = line.strip().split()
                            if len(parts) == 3:
                                data.append(parts)
                    except Exception as e:
                        self.LOGGER.exception(
                            "Error querying Jump-Bridge-Data at %s"
                            % (url_or_filepath,),
                            e,
                        )
                else:
                    data = Import().readGarpaFile(url_or_filepath)
                if len(data):  # valid File/URL
                    self.cache.put(
                        "jumpbridge_url", url_or_filepath, maxAge=Cache.FOREVER
                    )
            elif clipdata:
                data = Import().readGarpaFile(clipboard=clipdata)
            else:
                data = self.cache.fetch_jumpbridge_data()
            self.dotlan.setJumpbridges(data, self)
            if data and len(data):
                self.cache.put_jumpbridge_data(data)
        except Exception as e:
            QMessageBox.warning(
                None, "Loading Jump-Bridges failed!", "Error: %r" % (e,), QMessageBox.Ok
            )
            self.cache.delete("jumpbridge_url")
            self.cache.delete_jumpbridge_data()
        self.checkJumpbridges()

    # TODO: add functionality to still store other Region actions
    def handleRegionMenuItemSelected(self, menuAction=None):
        if menuAction:
            menuAction.setChecked(True)
            regionName = six.text_type(menuAction.property("regionName"))
            regionName = Regions.convertRegionName(regionName)
            RegionSettings().selected_region = regionName
            self.setupMap()

    def addMessageToIntelChat(self, message: Message):
        self.LOGGER.debug("Adding message to Intel: %r", message)
        scrollToBottom = False
        if (
            self.chatListWidget.verticalScrollBar().value()
            == self.chatListWidget.verticalScrollBar().maximum()
        ):
            scrollToBottom = True
        chatEntryWidget = ChatEntryWidget(message)
        message.widgets.append(chatEntryWidget)
        listWidgetItem = QtWidgets.QListWidgetItem(self.chatListWidget)
        listWidgetItem.setSizeHint(chatEntryWidget.sizeHint())
        self.chatListWidget.addItem(listWidgetItem)
        self.chatListWidget.setItemWidget(listWidgetItem, chatEntryWidget)
        self.avatarFindThread.addChatEntry(chatEntryWidget)
        self.chatEntries.append(chatEntryWidget)
        chatEntryWidget.mark_system.connect(self.markSystemOnMap)
        chatEntryWidget.ship_detail.connect(self.openShip)
        chatEntryWidget.enemy_detail.connect(self.openEnemy)
        self.chat_message_added.emit(chatEntryWidget)
        self.pruneMessages()
        if scrollToBottom:
            self.chatListWidget.scrollToBottom()

    def openEnemy(self, playerId):
        if playerId:
            zKill = "https://zkillboard.com/character/{}".format(playerId)
            webbrowser.open(zKill)
        pass

    @staticmethod
    def openShip(shipName):
        shipId = EsiHelper().getShipId(shipName)
        if shipId:
            zKill = "https://zkillboard.com/ship/{}".format(shipId)
            webbrowser.open(zKill)

    def pruneMessages(self):
        eve_now = time.mktime(EsiInterface().currentEveTime().timetuple())
        start = self.chatListWidget.count()
        for row in range(start):
            item = self.chatListWidget.item(0)
            widget = self.chatListWidget.itemWidget(item)
            message = self.chatListWidget.itemWidget(item).message
            diff = eve_now - time.mktime(message.utc_time.timetuple())
            try:
                if int(diff) > int(self.message_expiry):
                    self.chatEntries.remove(widget)
                    self.chatListWidget.takeItem(0)
            except Exception as e:
                self.LOGGER.error("Age is {diff} and expiry is {exp}: %r".format(diff=diff, exp=self.message_expiry), e)
        cleared = start - self.chatListWidget.count()
        if cleared:
            self.chatListWidget.scrollToBottom()
            self.LOGGER.debug("Cleared {} chat-messages".format(cleared))

    # def showKosResult(self, state, text, requestType, hasKos):
    #     if not self.scanIntelForKosRequestsEnabled:
    #         return
    #     try:
    #         if hasKos:
    #             SoundManager().playSound("kos", text)
    #         if state == "ok":
    #             if requestType == "xxx":  # An xxx request out of the chat
    #                 self.trayIcon.showMessage("Player KOS-Check", text, 1)
    #             elif requestType == "clipboard":  # request from clipboard-change
    #                 if len(text) <= 0:
    #                     text = "None KOS"
    #                 self.trayIcon.showMessage("Your KOS-Check", text, 1)
    #             text = text.replace("\n\n", "<br>")
    #             message = ChatParser.chat.Message("Vintel KOS-Check", text,
    #                                                     EsiInterface().currentEveTime(), "VINTEL",
    #                                                     [], states.NOT_CHANGE, text.upper(), text)
    #             self.addMessageToIntelChat(message)
    #         elif state == "error":
    #             self.trayIcon.showMessage("KOS Failure", text, 3)
    #     except Exception:
    #         pass
    #     self.trayIcon.setIcon(self.taskbarIconQuiescent)
    #

    def showInfo(self):
        self.LOGGER.debug("Opening About-Dialog")
        info_dialog = QDialog(self)
        loadUi("vi/ui/Info.ui", info_dialog)
        info_dialog.setModal(True)
        info_dialog.versionLabel.setText(u"Version: {0}".format(vi.version.DISPLAY))
        info_dialog.logoLabel.setPixmap(QtGui.QPixmap(resourcePath("logo.png")))
        info_dialog.closeButton.clicked.connect(info_dialog.accept)
        info_dialog.exec()
        self.LOGGER.debug("Closed About-Dialog")

    def showSoundSetup(self):
        self.settings(2)
        # sd = SoundSettingDialog(self)
        # sd.show()

    def systemTrayActivated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isMinimized():
                self.showNormal()
                self.activateWindow()
            elif not self.isActiveWindow():
                self.activateWindow()
            else:
                self.showMinimized()

    def updateAvatarOnChatEntry(self, chatEntry, avatarData):
        updated = chatEntry.updateAvatar(avatarData)
        if not updated:
            self.avatarFindThread.addChatEntry(chatEntry, clearCache=True)
        else:
            self.avatar_loaded.emit(chatEntry.message.user, avatarData)

    def updateMessageDetailsOnChatEntry(self, message: Message):
        for widget in message.widgets:
            widget.updateText()

    def checkPlayerLocations(self):
        if len(self.knownPlayers) == 0:
            # this is worth an Alert
            pass
        check = False
        for character in self.knownPlayers.keys():
            if (
                self.knownPlayers[character].monitor
                and self.knownPlayers[character].location
            ):
                check = True
        if not check:
            # Alert the User
            pass

    def logFileChanged(self, message: Message):
        self.LOGGER.debug("Message received: {}".format(message))
        # wait for Map to be completly loaded
        if message.status == State["LOCATION"]:
            self.knownPlayers[message.user].setLocation(message.systems[0])
            self.set_player_location(message.user, message.systems[0])
        elif message.status == State["SOUND_TEST"]:
            SoundManager().playSound("alarm", message)

        elif message.status == State["KOS_STATUS_REQUEST"]:
            # Do not accept KOS requests from any but monitored intel channels
            # as we don't want to encourage the use of xxx in those channels.
            if message.room not in self.roomnames:
                text = message.message[4:]
                text = text.replace("  ", ",")
                parts = (name.strip() for name in text.split(","))
                self.trayIcon.setIcon(self.taskbarIconWorking)
                self.kosRequestThread.addRequest(parts, "xxx", False)
        # Otherwise consider it a 'normal' chat message
        elif (
            message.user not in ("EVE-System", "EVE System")
            and message.status != State["IGNORE"]
        ):
            self.addMessageToIntelChat(message)
            # For each system that was mentioned in the message, check for alarm distance
            # to the current system and alarm if within alarm distance.
            systemList = self.dotlan.systems
            if message.systems:
                for system in message.systems:
                    systemname = system.name
                    try:
                        systemList[systemname].setStatus(
                            message.status, message.timestamp
                        )
                    except KeyError:  # Map-System may have changed in the mean time
                        pass
                    activePlayers = self.knownPlayers.getActiveNames()
                    # notify User if we don't have locations for active Players
                    self.checkPlayerLocations()
                    if message.status in (State["REQUEST"], State["ALARM"]) and (
                        message.user not in activePlayers or self.selfNotify
                    ):
                        alarmDistance = (
                            self.alarmDistance
                            if message.status == State["ALARM"]
                            else 0
                        )
                        for nSystem, data in system.getNeighbours(
                            alarmDistance
                        ).items():
                            distance = data["distance"]
                            chars = nSystem.getLocatedCharacters()
                            if len(chars) > 0 and self.popup_notification:
                                self.trayIcon.showNotification(
                                    message, system.name, ", ".join(chars), distance
                                )

        self.updateMapView()
