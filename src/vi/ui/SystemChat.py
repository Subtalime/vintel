# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SystemChat.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.resize(343, 300)
        Dialog.setMinimumSize(QtCore.QSize(0, 0))
        Dialog.setModal(False)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.chat = QtWidgets.QListWidget(Dialog)
        self.chat.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.chat.setObjectName("chat")
        self.verticalLayout.addWidget(self.chat)
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setMinimumSize(QtCore.QSize(0, 31))
        self.widget.setObjectName("widget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_3.setSpacing(5)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.closeButton = QtWidgets.QPushButton(self.widget)
        self.closeButton.setObjectName("closeButton")
        self.verticalLayout_3.addWidget(self.closeButton)
        self.gridLayout_2.addLayout(self.verticalLayout_3, 2, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(5, 7, 5, 0)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.location_vlayout = QtWidgets.QVBoxLayout()
        self.location_vlayout.setSpacing(2)
        self.location_vlayout.setObjectName("location_vlayout")
        self.playerNamesBox = QtWidgets.QComboBox(self.widget)
        self.playerNamesBox.setObjectName("playerNamesBox")
        self.location_vlayout.addWidget(self.playerNamesBox)
        self.locationButton = QtWidgets.QPushButton(self.widget)
        self.locationButton.setObjectName("locationButton")
        self.location_vlayout.addWidget(self.locationButton)
        self.horizontalLayout.addLayout(self.location_vlayout)
        self.status_vlayout = QtWidgets.QVBoxLayout()
        self.status_vlayout.setSpacing(2)
        self.status_vlayout.setObjectName("status_vlayout")
        self.alarmButton = QtWidgets.QPushButton(self.widget)
        self.alarmButton.setObjectName("alarmButton")
        self.status_vlayout.addWidget(self.alarmButton)
        self.clearButton = QtWidgets.QPushButton(self.widget)
        self.clearButton.setObjectName("clearButton")
        self.status_vlayout.addWidget(self.clearButton)
        self.horizontalLayout.addLayout(self.status_vlayout)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.widget)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.closeButton.setText(_translate("Dialog", "Close"))
        self.locationButton.setText(_translate("Dialog", "Set Char Location"))
        self.alarmButton.setText(_translate("Dialog", "Set alarm"))
        self.clearButton.setText(_translate("Dialog", "Set clear"))
