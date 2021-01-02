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

import logging
import sys
import time
import webbrowser

import requests
import six
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPoint, QPointF, pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QMainWindow,
    QMessageBox,
    QStyle,
    QStyleOption,
    QStylePainter,
    QSystemTrayIcon,
)

import vi.version
from vi.about.dialog import AboutDialog
from vi.cache.cache import Cache
from vi.character.CharacterMenu import CharacterMenu, Characters
from vi.chat.chatentrywidget import ChatEntryWidget
from vi.chat.chatmessage import Message
from vi.chat.systemchat import SystemChat
from vi.color.helpers import contrast_color, string_to_color
from vi.dotlan.exception import DotlanException
from vi.dotlan.mymap import MyMap
from vi.dotlan.regions import Regions, convert_region_name
from vi.esi import EsiInterface
from vi.esi.esihelper import EsiHelper
from vi.jumpbridge.jumpbridgedialog import JumpBridgeDialog
from vi.logger.logconfig import LogConfigurationThread
from vi.logger.logwindow import LogWindow
from vi.stopwatch.mystopwatch import ViStopwatch
from vi.region.RegionMenu import RegionMenu
from vi.resources import resourcePath, getVintelDir
from vi.settings.settings import GeneralSettings, RegionSettings
from vi.settings.SettingsDialog import SettingsDialog
from vi.sound.soundmanager import SoundManager
from vi.states import State
from vi.systemtray import TrayContextMenu, TrayIcon
from vi.threads import *
from vi.threads.chatmonitor import ChatMonitorThread
from vi.threads.filewatcher import FileWatcherThread
from vi.ui.MainWindow import Ui_MainWindow
from vi.version import NotifyNewVersionThread

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

    def initialize(self, path_to_logs: str, tray_icon: TrayIcon, background_color: str):
        self.LOGGER = logging.getLogger(__name__)
        self.stopWatch = ViStopwatch()
        self.LOGGER.debug("LogWindow create...")
        self.logWindow = LogWindow()
        self.LOGGER.debug("LogWindow done")
        # let's hope, this will speed up start-up
        self.LOGGER.debug("EsiInterface create...")
        EsiInterface(cache_dir=getVintelDir())
        self.LOGGER.debug("EsiInterface done")
        self.resize(1363, 880)
        self.splitter.setSizes([1065, 239])
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
        self.trayIcon.activated.connect(self.system_tray_activated)
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.clipboard.clear(mode=self.clipboard.Clipboard)
        self.changeAlarmDistance(GeneralSettings().alarm_distance)
        self.frameButton.setVisible(False)

        # Load toon names of this User
        self.knownPlayers = Characters()
        # here we are resetting our own menus, not the one from UI
        self.menuCharacters = CharacterMenu("Characters", self)
        self.menubar.insertMenu(self.menuSound.menuAction(), self.menuCharacters)
        # TODO: not working yet, so disable
        # self.menuCharacters.setEnabled(False)
        self.updateCharacterMenu()
        self.menuRegion = RegionMenu("Regions", self)
        self.menubar.insertMenu(self.menuSound.menuAction(), self.menuRegion)
        # Disable the sound UI if sound is not available
        self.changeSound(disable=not SoundManager().soundAvailable)

        # Set up Transparency menu - fill in opacity values and make connections
        self.opacityGroup = QActionGroup(self.menubar)
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

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        # set the Splitter-Location
        self.splitter.setStretchFactor(8, 2)
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
        self.backgroundColor = None
        self.LOGGER = None
        self.stopWatch = None
        self.logWindow = None
        self.cache = None
        self.content = None
        self.initialMapPosition = None
        self.initialZoom = None
        self.lastStatisticsUpdate = 0
        self.chatEntries = []
        self.message_expiry = None
        self.refreshContent = None
        self.pathToLogs = None
        self.clipboardTimer = None
        self.oldClipboardContent = None
        self.trayIcon = None
        self.clipboard = None
        self.taskbarIconWorking = None
        self.taskbarIconQuiescent = None
        self.map_update_interval = None
        self.opacityGroup = None
        self.scanIntelForKosRequestsEnabled = False
        self.mapPositionsDict = {}
        # Load toon names of this User
        self.knownPlayers = None
        # here we are resetting our own menus, not the one from UI
        self.menuCharacters = None
        self.menuRegion = None

    def splitter_location(self, pos, index):
        self.LOGGER.debug("Splitter Pos %d, Index %d, Geometry %r, State %r", pos, index, self.splitter.geometry(), self.splitter.saveState())

    def setColor(self, color: str = None) -> str:
        if color:
            self.backgroundColor = color
            color = string_to_color(self.backgroundColor)
            # if WHITE, then reset to default PyQt Style
            if color.name() != "#ffffff":
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
            self.menuCharacters.remove_characters()
            self.LOGGER.debug(
                "Updating Character-Menu with Players: {}".format(self.knownPlayers)
            )
            self.menuCharacters.add_characters(self.knownPlayers)
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
        self.statisticsButton.clicked.connect(self.set_dotlan_statistics_visibility)
        self.jumpbridgesButton.clicked.connect(self.set_dotlan_jumpbridge_visibility)
        self.chatLargeButton.clicked.connect(self.chatLarger)
        self.chatSmallButton.clicked.connect(self.chatSmaller)
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.showChatAvatarsAction.triggered.connect(self.changeShowAvatars)
        self.alwaysOnTopAction.triggered.connect(self.changeAlwaysOnTop)
        self.chooseChatRoomsAction.triggered.connect(self.showChatroomChooser)

        self.showChatAction.triggered.connect(self.changeChatVisibility)
        self.soundSetupAction.triggered.connect(self.edit_sound_setup)
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

    def region_menu_update(self):
        self.menuRegion.addItems()

    def viewChatlogs(self):
        logs = ""
        for log in self.chatThread.process_pool.keys():
            logs += "{}\r\n".format(log)
        QMessageBox.information(None, "Monitored logs", "%s" % logs, QMessageBox.Ok)

    def settings(self, tabIndex: int = 0) -> bool:

        setting = SettingsDialog(self, tabIndex)

        setting.show()
        # return True if Changes have been applied
        if setting.exec_():
            if self.backgroundColor != GeneralSettings().background_color:
                self.setColor(GeneralSettings().background_color)
            # self.enableCharacterParser(GeneralSettings().character_parser)
            # self.enableShipParser(GeneralSettings().ship_parser)
            self.enablePopupNotification(GeneralSettings().popup_notification)
            self.clipboardCheckInterval(GeneralSettings().clipboard_check_interval)
            self.messageExpiry(GeneralSettings().message_expiry)
            self.enableSelfNotify(GeneralSettings().self_notify)
            self.changeAlarmDistance(GeneralSettings().alarm_distance)
            self.region_menu_update()
            return True
        return False

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
            if RegionSettings().selected_region != qAction.text():
                RegionSettings().selected_region = qAction.text()
                self.LOGGER.debug("Set Region to {}".format(qAction.text()))
                self.setupMap()

    # Dialog to select Regions to monitor
    def showRegionChooser(self):
        self.settings(3)

    def updatePlayers(self, player_list: list):
        self.knownPlayers.add_names(player_list)
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
        self.avatarFindThread = AvatarThread()
        self.avatarFindThread.avatar_update.connect(self.updateAvatarOnChatEntry)
        self.avatarFindThread.start()

        # self.kosRequestThread = KOSCheckerThread()
        # self.kosRequestThread.kos_result.connect(self.showKosResult)
        # self.kosRequestThread.start()

        self.chatThread = ChatMonitorThread()
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

        self.chatTidyThread = ChatTidyUpThread(self.message_expiry)
        self.chatTidyThread.time_up.connect(self.pruneMessages)
        self.chatTidyThread.start()

        self.statisticsThread = StatisticsThread()
        self.statisticsThread.statistic_data_update.connect(self.updateStatisticsOnMap)
        # statisticsThread is blocked until first call of requestStatistics
        self.statisticsThread.start()

        self.LOGGER.debug("Finished Creating threads")

    # TODO: store each system configured in Regions
    # TODO: therefore if we switch Region, we can update with previously found data
    # TODO: when clicking on System in Chat, scroll to the position within the Map
    def setupMap(self, initialize=False):
        if self.mapUpdateThread:
            self.mapUpdateThread.pause(True)
        self.LOGGER.debug("Finding map file")
        regionName = RegionSettings().selected_region
        if not regionName:
            regionName = "Delve"
        regionName = convert_region_name(regionName)
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
        with self.stopWatch.timer("update_jumpbridges"):
            self.update_jumpbridges()
        self.dotlan.setJumpbridgesVisibility(self.is_jumpbridge_visible())
        self.dotlan.setStatisticsVisibility(self.is_statistic_visible())
        self.LOGGER.debug(self.stopWatch.get_report())
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
            except TimeoutError:
                pass
            self.clipboardTimer.stop()

    def restartClipboardTimer(self):
        self.stopClipboardTimer()
        self.startClipboardTimer()

    def save_settings(self):
        # Known playernames
        self.knownPlayers.store_data()
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
            (None, "changeSound", self.activateSoundAction.isChecked()),
            (None, "changeChatVisibility", self.showChatAction.isChecked()),
            (None, "loadInitialMapPositions", self.mapPositionsDict),
            (None, "changeFrameless", self.framelessWindowAction.isChecked()),
            (
                None,
                "changeUseSpokenNotifications",
                self.useSpokenNotificationsAction.isChecked(),
            ),
            # (
            #     None,
            #     "changeKosCheckClipboard",
            #     self.kosClipboardActiveAction.isChecked(),
            # ),
            (None, "changeAutoScanIntel", self.scanIntelForKosRequestsEnabled),
        )
        self.cache.save_settings("settings", settings, 60 * 60 * 24 * 30)

    def closeEvent(self, event):
        """
            Persisting things to the cache before closing the window
        """
        self.save_settings()
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
        super(MainWindow, self).closeEvent(event)

    def notifyNewerVersion(self, newestVersion):
        msg = (
            "An update is available for {}. Current V{} to V{}\n"
            "Consider upgrading by visiting {}".format(
                vi.version.PROGNAME, vi.version.VERSION, newestVersion, vi.version.URL
            )
        )
        self.LOGGER.info(msg)
        self.trayIcon.showMessage("Newer Version", msg)

    def changeChatVisibility(self, new_value=None):
        if new_value is None:
            new_value = self.showChatAction.isChecked()
        self.showChatAction.setChecked(new_value)
        self.chatbox.setVisible(new_value)

    def changeKosCheckClipboard(self, new_value=None):
        if new_value is None:
            new_value = self.kosClipboardActiveAction.isChecked()
        self.kosClipboardActiveAction.setChecked(new_value)
        if new_value:
            self.startClipboardTimer()
        else:
            self.stopClipboardTimer()

    def changeAutoScanIntel(self, new_value=None):
        if new_value is None:
            new_value = self.autoScanIntelAction.isChecked()
        self.autoScanIntelAction.setChecked(new_value)
        self.scanIntelForKosRequestsEnabled = new_value

    def changeUseSpokenNotifications(self, new_value=None):
        if SoundManager().platformSupportsSpeech():
            if new_value is None:
                new_value = self.useSpokenNotificationsAction.isChecked()
            self.useSpokenNotificationsAction.setChecked(new_value)
            SoundManager().setUseSpokenNotifications(new_value)
        else:
            self.useSpokenNotificationsAction.setChecked(False)
            self.useSpokenNotificationsAction.setEnabled(False)

    def changeOpacity(self, new_value=None):
        try:
            action = self.opacityGroup.checkedAction()
            new_value = action.opacity
            if new_value is not None:
                for action in self.opacityGroup.actions():
                    if action.opacity == new_value:
                        action.setChecked(True)
                        break
            self.setWindowOpacity(action.opacity)
        except Exception as e:
            self.LOGGER.error("Error while selecting Opacity", e)

    def changeSound(self, new_value=None, disable=False):
        if disable:
            self.activateSoundAction.setChecked(False)
            self.activateSoundAction.setEnabled(False)
            self.soundSetupAction.setEnabled(False)
            # self.soundButton.setEnabled(False)
            QMessageBox.warning(
                self,
                "Sound disabled",
                "The lib 'pyglet' which is used to play sounds cannot "
                "be found, so the soundsystem is disabled.\nIf you want sound, "
                "please install the 'pyglet' library. This warning will "
                "not be shown again.",
                QMessageBox.Ok,
            )
        else:
            self.soundSetupAction.setEnabled(True)
            if new_value is None:
                new_value = GeneralSettings().sound_active
            self.activateSoundAction.setChecked(new_value)
            self.soundSetupAction.setEnabled(new_value)
            GeneralSettings().sound_active = new_value
            self.LOGGER.info("Sound activation changed to %r", new_value)

    def changeAlwaysOnTop(self, new_value=None):
        if new_value is None:
            new_value = self.alwaysOnTopAction.isChecked()
        self.hide()
        self.alwaysOnTopAction.setChecked(new_value)
        if new_value:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & (~QtCore.Qt.WindowStaysOnTopHint))
        self.show()

    def changeFrameless(self, new_value=None):
        if new_value is None:
            new_value = not self.frameButton.isVisible()
        self.hide()
        if new_value:
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            self.changeAlwaysOnTop(True)
        else:
            self.setWindowFlags(self.windowFlags() & (~QtCore.Qt.FramelessWindowHint))
        self.menubar.setVisible(not new_value)
        self.frameButton.setVisible(new_value)
        self.framelessWindowAction.setChecked(new_value)

        for cm in TrayContextMenu.instances:
            cm.framelessCheck.setChecked(new_value)
        self.show()

    def changeShowAvatars(self, new_value=None):
        if new_value is None:
            new_value = self.showChatAvatarsAction.isChecked()
        self.showChatAvatarsAction.setChecked(new_value)
        ChatEntryWidget.SHOW_AVATAR = new_value
        for entry in self.chatEntries:
            entry.avatarLabel.setVisible(new_value)

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

    # def enableCharacterParser(self, enable: bool = None) -> bool:
    #     if enable is not None:
    #         self.character_parser_enabled = enable
    #         self.character_parser.emit(enable)
    #     return self.character_parser_enabled
    #
    # def enableShipParser(self, enable: bool = None) -> bool:
    #     if enable is not None:
    #         self.ship_parser_enabled = enable
    #         self.ship_parser.emit(enable)
    #     return self.ship_parser_enabled
    #
    def changeAlarmDistance(self, distance: int):
        self.alarmDistance = int(distance)
        for action in self.trayIcon.context_menu.distanceGroup.actions():
            if action.alarmDistance == distance:
                action.setChecked(True)
        self.trayIcon.alarmDistance = int(distance)

    def is_jumpbridge_visible(self):
        return self.jumpbridgesButton.isChecked()

    def set_dotlan_jumpbridge_visibility(self):
        """the button is only enabled if we have valid Jump-Bridges.
        """
        self.LOGGER.debug("JumpBridge-Button clicked: %s", self.is_jumpbridge_visible())
        self.update_jumpbridges()
        self.dotlan.setJumpbridgesVisibility(self.is_jumpbridge_visible())
        self.updateMapView()

    def is_statistic_visible(self):
        return self.statisticsButton.isChecked()

    def set_dotlan_statistics_visibility(self):
        self.dotlan.setStatisticsVisibilyt(self.is_statistic_visible())
        self.updateMapView()
        if self.is_statistic_visible():
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
        """force a Refresh of the Map in screen.
        """
        scrollPosition = self.mapView.page().scrollPosition()
        zoom = self.mapView.page().zoomFactor()
        if self.initialMapPosition:
            scrollPosition = self.initialMapPosition
            zoom = self.initialZoom
            self.initialMapPosition = self.initialZoom = None
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
        if not regionName:
            regionName = self.cache.fetch("region_name")
        if regionName and regionName in self.mapPositionsDict.keys():
            xy, zoom = self.mapPositionsDict[regionName]
            self.initialMapPosition = QPoint(xy[0], xy[1])
            self.initialZoom = zoom

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
        else:
            self.logWindow.hide()

    def showChatroomChooser(self):
        self.settings(4)

    def showJumpBridgeChooser(self):
        chooser = JumpBridgeDialog(self)
        chooser.set_jump_bridge_url.connect(self.update_jumpbridges)
        chooser.exec_()

    # TODO: new settings
    def checkJumpbridges(self):
        """en-/disable Jumpbridge-Button on interface.
        """
        data = RegionSettings().jump_bridge_data
        if data:
            self.jumpbridgesButton.setEnabled(True)
            self.jumpbridgesButton.setCheckable(True)
            # self.jumpbridgesButton.setChecked(False)
        else:
            self.jumpbridgesButton.setEnabled(False)
            self.jumpbridgesButton.setCheckable(False)
            self.jumpbridgesButton.setChecked(False)

    # TODO: new settings
    def update_jumpbridges(self):
        data = RegionSettings().jump_bridge_data
        self.dotlan.setJumpbridges(data, self)
        self.checkJumpbridges()

    # TODO: add functionality to still store other Region actions
    def handleRegionMenuItemSelected(self, menuAction=None):
        if menuAction:
            menuAction.setChecked(True)
            regionName = six.text_type(menuAction.property("regionName"))
            regionName = Regions.convertRegionName(regionName)
            RegionSettings().selected_region = regionName
            self.setupMap()

    # TODO: here it would be good to have a list of Messages per Region
    # so, when changing Region, the current list of Messages could be
    # parsed and then added to the Map-Display
    def addMessageToIntelChat(self, message: Message):
        self.LOGGER.debug("Adding message to Intel: %r", message)
        scroll_to_bottom = False
        if (
            self.chatListWidget.verticalScrollBar().value()
            == self.chatListWidget.verticalScrollBar().maximum()
        ):
            scroll_to_bottom = True
        # create widget
        chatEntryWidget = ChatEntryWidget(message)
        message.widgets.append(chatEntryWidget)
        listWidgetItem = QtWidgets.QListWidgetItem(self.chatListWidget)
        listWidgetItem.setSizeHint(chatEntryWidget.sizeHint())
        # add widget to lost
        self.chatListWidget.addItem(listWidgetItem)
        self.chatListWidget.setItemWidget(listWidgetItem, chatEntryWidget)
        self.chatEntries.append(chatEntryWidget)
        # allow for Link-Clicks in widget
        chatEntryWidget.mark_system.connect(self.markSystemOnMap)
        chatEntryWidget.ship_detail.connect(self.openShip)
        chatEntryWidget.enemy_detail.connect(self.openEnemy)
        # find the Avatar
        self.avatarFindThread.add_chat_entry(chatEntryWidget)
        # let anyone else know that we added a widget
        self.chat_message_added.emit(chatEntryWidget)
        if scroll_to_bottom:
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
                self.LOGGER.error(
                    "Age is {diff} and expiry is {exp}: %r".format(
                        diff=diff, exp=self.message_expiry
                    ),
                    e,
                )
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

    def show_about_dialog(self):
        about = AboutDialog(self)
        about.exec_()

    def edit_sound_setup(self):
        self.settings(2)

    def system_tray_activated(self, reason):
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
            self.avatarFindThread.add_chat_entry(chatEntry, clearCache=True)
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

        # elif message.status == State["KOS_STATUS_REQUEST"]:
        #     # Do not accept KOS requests from any but monitored intel channels
        #     # as we don't want to encourage the use of xxx in those channels.
        #     if message.room not in self.roomnames:
        #         text = message.message[4:]
        #         text = text.replace("  ", ",")
        #         parts = (name.strip() for name in text.split(","))
        #         self.trayIcon.setIcon(self.taskbarIconWorking)
        #         self.kosRequestThread.addRequest(parts, "xxx", False)
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
                    activePlayers = self.knownPlayers.get_active_names()
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
                                self.LOGGER.debug("Submitted Tray-Icon-Notification")
                                self.trayIcon.showNotification(
                                    message, system.name, ", ".join(chars), distance
                                )

        self.updateMapView()
