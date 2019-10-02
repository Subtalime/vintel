# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(936, 695)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setEnabled(True)
        self.splitter.setFrameShape(QtWidgets.QFrame.Panel)
        self.splitter.setFrameShadow(QtWidgets.QFrame.Raised)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setOpaqueResize(True)
        self.splitter.setHandleWidth(6)
        self.splitter.setObjectName("splitter")
        self.mapwidget = QtWidgets.QWidget(self.splitter)
        self.mapwidget.setObjectName("mapwidget")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.mapwidget)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mapbuttonwidget = QtWidgets.QWidget(self.mapwidget)
        self.mapbuttonwidget.setMinimumSize(QtCore.QSize(0, 24))
        self.mapbuttonwidget.setBaseSize(QtCore.QSize(1024, 0))
        self.mapbuttonwidget.setObjectName("mapbuttonwidget")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.mapbuttonwidget)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.frameButton = QtWidgets.QPushButton(self.mapbuttonwidget)
        self.frameButton.setMaximumSize(QtCore.QSize(16777215, 19))
        self.frameButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.frameButton.setObjectName("frameButton")
        self.horizontalLayout_2.addWidget(self.frameButton)
        self.zoomInButton = QtWidgets.QPushButton(self.mapbuttonwidget)
        self.zoomInButton.setMaximumSize(QtCore.QSize(16777215, 19))
        self.zoomInButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.zoomInButton.setObjectName("zoomInButton")
        self.horizontalLayout_2.addWidget(self.zoomInButton)
        self.zoomOutButton = QtWidgets.QPushButton(self.mapbuttonwidget)
        self.zoomOutButton.setMaximumSize(QtCore.QSize(16777215, 19))
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(False)
        font.setWeight(50)
        self.zoomOutButton.setFont(font)
        self.zoomOutButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.zoomOutButton.setObjectName("zoomOutButton")
        self.horizontalLayout_2.addWidget(self.zoomOutButton)
        self.jumpbridgesButton = QtWidgets.QPushButton(self.mapbuttonwidget)
        self.jumpbridgesButton.setMaximumSize(QtCore.QSize(16777215, 19))
        self.jumpbridgesButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.jumpbridgesButton.setCheckable(True)
        self.jumpbridgesButton.setChecked(False)
        self.jumpbridgesButton.setObjectName("jumpbridgesButton")
        self.horizontalLayout_2.addWidget(self.jumpbridgesButton)
        self.statisticsButton = QtWidgets.QPushButton(self.mapbuttonwidget)
        self.statisticsButton.setMaximumSize(QtCore.QSize(16777215, 19))
        self.statisticsButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.statisticsButton.setCheckable(True)
        self.statisticsButton.setObjectName("statisticsButton")
        self.horizontalLayout_2.addWidget(self.statisticsButton)
        self.gridLayout_5.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.mapbuttonwidget)
        self.mapView = PanningWebView(self.mapwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mapView.sizePolicy().hasHeightForWidth())
        self.mapView.setSizePolicy(sizePolicy)
        self.mapView.setBaseSize(QtCore.QSize(1050, 790))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.mapView.setFont(font)
        self.mapView.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.mapView.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.mapView.setProperty("url", QtCore.QUrl("about:blank"))
        self.mapView.setObjectName("mapView")
        self.verticalLayout.addWidget(self.mapView)
        self.gridLayout_3.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.chatbox = QtWidgets.QGroupBox(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.chatbox.sizePolicy().hasHeightForWidth())
        self.chatbox.setSizePolicy(sizePolicy)
        self.chatbox.setBaseSize(QtCore.QSize(0, 0))
        self.chatbox.setObjectName("chatbox")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.chatbox)
        self.gridLayout_6.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_6.setHorizontalSpacing(5)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.chatLargeButton = QtWidgets.QPushButton(self.chatbox)
        self.chatLargeButton.setMaximumSize(QtCore.QSize(16777215, 15))
        self.chatLargeButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.chatLargeButton.setObjectName("chatLargeButton")
        self.horizontalLayout.addWidget(self.chatLargeButton)
        self.chatSmallButton = QtWidgets.QPushButton(self.chatbox)
        self.chatSmallButton.setMaximumSize(QtCore.QSize(16777215, 15))
        self.chatSmallButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.chatSmallButton.setObjectName("chatSmallButton")
        self.horizontalLayout.addWidget(self.chatSmallButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.chatListWidget = QtWidgets.QListWidget(self.chatbox)
        self.chatListWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.chatListWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.chatListWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.chatListWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.chatListWidget.setResizeMode(QtWidgets.QListView.Adjust)
        self.chatListWidget.setObjectName("chatListWidget")
        self.verticalLayout_2.addWidget(self.chatListWidget)
        self.gridLayout_6.addLayout(self.verticalLayout_2, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 936, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menuChat = QtWidgets.QMenu(self.menubar)
        self.menuChat.setObjectName("menuChat")
        self.menuSound = QtWidgets.QMenu(self.menubar)
        self.menuSound.setObjectName("menuSound")
        self.menuRegion = QtWidgets.QMenu(self.menubar)
        self.menuRegion.setObjectName("menuRegion")
        self.menuWindow = QtWidgets.QMenu(self.menubar)
        self.menuWindow.setObjectName("menuWindow")
        self.menuTransparency = QtWidgets.QMenu(self.menuWindow)
        self.menuTransparency.setObjectName("menuTransparency")
        self.menuCharacters = QtWidgets.QMenu(self.menubar)
        self.menuCharacters.setObjectName("menuCharacters")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        MainWindow.setMenuBar(self.menubar)
        self.infoAction = QtWidgets.QAction(MainWindow)
        self.infoAction.setObjectName("infoAction")
        self.alwaysOnTopAction = QtWidgets.QAction(MainWindow)
        self.alwaysOnTopAction.setCheckable(True)
        self.alwaysOnTopAction.setChecked(False)
        self.alwaysOnTopAction.setObjectName("alwaysOnTopAction")
        self.opac100 = QtWidgets.QAction(MainWindow)
        self.opac100.setObjectName("opac100")
        self.opac80 = QtWidgets.QAction(MainWindow)
        self.opac80.setObjectName("opac80")
        self.opac60 = QtWidgets.QAction(MainWindow)
        self.opac60.setObjectName("opac60")
        self.opac40 = QtWidgets.QAction(MainWindow)
        self.opac40.setObjectName("opac40")
        self.opac20 = QtWidgets.QAction(MainWindow)
        self.opac20.setObjectName("opac20")
        self.chooseChatRoomsAction = QtWidgets.QAction(MainWindow)
        self.chooseChatRoomsAction.setCheckable(False)
        self.chooseChatRoomsAction.setChecked(False)
        self.chooseChatRoomsAction.setObjectName("chooseChatRoomsAction")
        self.showChatAvatarsAction = QtWidgets.QAction(MainWindow)
        self.showChatAvatarsAction.setCheckable(True)
        self.showChatAvatarsAction.setChecked(True)
        self.showChatAvatarsAction.setObjectName("showChatAvatarsAction")
        self.kosClipboardActiveAction = QtWidgets.QAction(MainWindow)
        self.kosClipboardActiveAction.setCheckable(True)
        self.kosClipboardActiveAction.setChecked(False)
        self.kosClipboardActiveAction.setObjectName("kosClipboardActiveAction")
        self.showChatAction = QtWidgets.QAction(MainWindow)
        self.showChatAction.setCheckable(True)
        self.showChatAction.setChecked(True)
        self.showChatAction.setObjectName("showChatAction")
        self.activateSoundAction = QtWidgets.QAction(MainWindow)
        self.activateSoundAction.setCheckable(True)
        self.activateSoundAction.setChecked(True)
        self.activateSoundAction.setObjectName("activateSoundAction")
        self.framelessWindowAction = QtWidgets.QAction(MainWindow)
        self.framelessWindowAction.setCheckable(True)
        self.framelessWindowAction.setObjectName("framelessWindowAction")
        self.quitAction = QtWidgets.QAction(MainWindow)
        self.quitAction.setObjectName("quitAction")
        self.chooseRegionAction = QtWidgets.QAction(MainWindow)
        self.chooseRegionAction.setCheckable(True)
        self.chooseRegionAction.setObjectName("chooseRegionAction")
        self.soundSetupAction = QtWidgets.QAction(MainWindow)
        self.soundSetupAction.setObjectName("soundSetupAction")
        self.jumpbridgeDataAction = QtWidgets.QAction(MainWindow)
        self.jumpbridgeDataAction.setObjectName("jumpbridgeDataAction")
        self.useSpokenNotificationsAction = QtWidgets.QAction(MainWindow)
        self.useSpokenNotificationsAction.setCheckable(True)
        self.useSpokenNotificationsAction.setObjectName("useSpokenNotificationsAction")
        self.autoScanIntelAction = QtWidgets.QAction(MainWindow)
        self.autoScanIntelAction.setCheckable(True)
        self.autoScanIntelAction.setChecked(True)
        self.autoScanIntelAction.setVisible(True)
        self.autoScanIntelAction.setIconVisibleInMenu(False)
        self.autoScanIntelAction.setObjectName("autoScanIntelAction")
        self.actionAlway_On_Top = QtWidgets.QAction(MainWindow)
        self.actionAlway_On_Top.setObjectName("actionAlway_On_Top")
        self.actionFrameless = QtWidgets.QAction(MainWindow)
        self.actionFrameless.setObjectName("actionFrameless")
        self.actionTransparency = QtWidgets.QAction(MainWindow)
        self.actionTransparency.setObjectName("actionTransparency")
        self.queriousRegionAction_2 = QtWidgets.QAction(MainWindow)
        self.queriousRegionAction_2.setCheckable(True)
        self.queriousRegionAction_2.setObjectName("queriousRegionAction_2")
        self.delveRegionAction = QtWidgets.QAction(MainWindow)
        self.delveRegionAction.setCheckable(True)
        self.delveRegionAction.setObjectName("delveRegionAction")
        self.delveQueriousRegionAction = QtWidgets.QAction(MainWindow)
        self.delveQueriousRegionAction.setCheckable(True)
        self.delveQueriousRegionAction.setObjectName("delveQueriousRegionAction")
        self.delveQueriousCompactRegionAction = QtWidgets.QAction(MainWindow)
        self.delveQueriousCompactRegionAction.setCheckable(True)
        self.delveQueriousCompactRegionAction.setObjectName("delveQueriousCompactRegionAction")
        self.queriousRegionAction = QtWidgets.QAction(MainWindow)
        self.queriousRegionAction.setCheckable(True)
        self.queriousRegionAction.setObjectName("queriousRegionAction")
        self.actionLogging = QtWidgets.QAction(MainWindow)
        self.actionLogging.setObjectName("actionLogging")
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionSettings = QtWidgets.QAction(MainWindow)
        self.actionSettings.setObjectName("actionSettings")
        self.menu.addAction(self.autoScanIntelAction)
        self.menu.addAction(self.kosClipboardActiveAction)
        self.menu.addSeparator()
        self.menuChat.addAction(self.showChatAction)
        self.menuChat.addAction(self.chooseChatRoomsAction)
        self.menuChat.addAction(self.showChatAvatarsAction)
        self.menuSound.addAction(self.activateSoundAction)
        self.menuSound.addAction(self.soundSetupAction)
        self.menuSound.addSeparator()
        self.menuSound.addAction(self.useSpokenNotificationsAction)
        self.menuWindow.addAction(self.alwaysOnTopAction)
        self.menuWindow.addAction(self.framelessWindowAction)
        self.menuWindow.addAction(self.menuTransparency.menuAction())
        self.menuWindow.addAction(self.actionLogging)
        self.menuWindow.addSeparator()
        self.menuWindow.addAction(self.actionAbout)
        self.menuFile.addAction(self.actionQuit)
        self.menuEdit.addAction(self.actionSettings)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menuChat.menuAction())
        self.menubar.addAction(self.menuCharacters.menuAction())
        self.menubar.addAction(self.menuSound.menuAction())
        self.menubar.addAction(self.menuRegion.menuAction())
        self.menubar.addAction(self.menuWindow.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Vintel"))
        self.frameButton.setText(_translate("MainWindow", "Restore Frame"))
        self.zoomInButton.setText(_translate("MainWindow", "+"))
        self.zoomOutButton.setText(_translate("MainWindow", "-"))
        self.jumpbridgesButton.setText(_translate("MainWindow", "Jump Bridges"))
        self.statisticsButton.setText(_translate("MainWindow", "Statistics"))
        self.chatbox.setTitle(_translate("MainWindow", "All Intel (past 20 minutes)"))
        self.chatLargeButton.setText(_translate("MainWindow", "+"))
        self.chatSmallButton.setText(_translate("MainWindow", "-"))
        self.menu.setTitle(_translate("MainWindow", "Kos"))
        self.menuChat.setTitle(_translate("MainWindow", "Chat"))
        self.menuSound.setTitle(_translate("MainWindow", "Sound"))
        self.menuRegion.setTitle(_translate("MainWindow", "Region"))
        self.menuWindow.setTitle(_translate("MainWindow", "Window"))
        self.menuTransparency.setTitle(_translate("MainWindow", "Transparency"))
        self.menuCharacters.setTitle(_translate("MainWindow", "Characters"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.infoAction.setText(_translate("MainWindow", "Info"))
        self.alwaysOnTopAction.setText(_translate("MainWindow", "Always On Top"))
        self.opac100.setText(_translate("MainWindow", "Opacity 100%"))
        self.opac80.setText(_translate("MainWindow", "Opacity 80%"))
        self.opac60.setText(_translate("MainWindow", "Opacity 60%"))
        self.opac40.setText(_translate("MainWindow", "Opacity 40%"))
        self.opac20.setText(_translate("MainWindow", "Opacity 20%"))
        self.chooseChatRoomsAction.setText(_translate("MainWindow", "Choose Chatrooms..."))
        self.showChatAvatarsAction.setText(_translate("MainWindow", "Show Chat Avatars"))
        self.kosClipboardActiveAction.setText(_translate("MainWindow", "Auto KOS-Check Clipboard"))
        self.kosClipboardActiveAction.setToolTip(_translate("MainWindow", "Activate Clipboard KOS-Check"))
        self.showChatAction.setText(_translate("MainWindow", "Show Chat"))
        self.activateSoundAction.setText(_translate("MainWindow", "Activate Sound"))
        self.framelessWindowAction.setText(_translate("MainWindow", "Frameless Main Window"))
        self.framelessWindowAction.setToolTip(_translate("MainWindow", "Frameless Main Window"))
        self.quitAction.setText(_translate("MainWindow", "Quit"))
        self.chooseRegionAction.setText(_translate("MainWindow", "Other Region..."))
        self.soundSetupAction.setText(_translate("MainWindow", "Sound Setup..."))
        self.jumpbridgeDataAction.setText(_translate("MainWindow", "Jumpbridge Data..."))
        self.useSpokenNotificationsAction.setText(_translate("MainWindow", "Spoken Notifications"))
        self.useSpokenNotificationsAction.setToolTip(_translate("MainWindow", "Spoken KOS results"))
        self.autoScanIntelAction.setText(_translate("MainWindow", "Scan Intel For Requests"))
        self.autoScanIntelAction.setToolTip(_translate("MainWindow", "When enabled, scans intel for xxx kos requests"))
        self.actionAlway_On_Top.setText(_translate("MainWindow", "Always On Top"))
        self.actionFrameless.setText(_translate("MainWindow", "Frameless"))
        self.actionTransparency.setText(_translate("MainWindow", "Transparency"))
        self.queriousRegionAction_2.setText(_translate("MainWindow", "Querious"))
        self.queriousRegionAction_2.setProperty("regionName", _translate("MainWindow", "querious"))
        self.delveRegionAction.setText(_translate("MainWindow", "Delve"))
        self.delveRegionAction.setProperty("regionName", _translate("MainWindow", "delve"))
        self.delveQueriousRegionAction.setText(_translate("MainWindow", "Delve / Querious"))
        self.delveQueriousRegionAction.setProperty("regionName", _translate("MainWindow", "delvequerious"))
        self.delveQueriousCompactRegionAction.setText(_translate("MainWindow", "Delve / Querious (compact)"))
        self.delveQueriousCompactRegionAction.setProperty("regionName", _translate("MainWindow", "delve-querious"))
        self.queriousRegionAction.setText(_translate("MainWindow", "Querious"))
        self.queriousRegionAction.setProperty("regionName", _translate("MainWindow", "querious"))
        self.actionLogging.setText(_translate("MainWindow", "Logging"))
        self.actionAbout.setText(_translate("MainWindow", "About"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        self.actionSettings.setText(_translate("MainWindow", "Settings..."))


from vi.PanningWebView import PanningWebView
