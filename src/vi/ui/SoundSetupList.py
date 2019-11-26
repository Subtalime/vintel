# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SoundSetupList.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(534, 421)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lstSound = QtWidgets.QTableView(Dialog)
        self.lstSound.setObjectName("lstSound")
        self.verticalLayout.addWidget(self.lstSound)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.btnPlay = QtWidgets.QPushButton(Dialog)
        self.btnPlay.setObjectName("btnPlay")
        self.gridLayout_2.addWidget(self.btnPlay, 1, 3, 1, 1)
        self.volumeSlider = QtWidgets.QSlider(Dialog)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setTracking(False)
        self.volumeSlider.setOrientation(QtCore.Qt.Vertical)
        self.volumeSlider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.volumeSlider.setObjectName("volumeSlider")
        self.gridLayout_2.addWidget(self.volumeSlider, 1, 4, 1, 1)
        self.txtSound = QtWidgets.QLineEdit(Dialog)
        self.txtSound.setObjectName("txtSound")
        self.gridLayout_2.addWidget(self.txtSound, 1, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 1, 0, 1, 1)
        self.btnSearch = QtWidgets.QPushButton(Dialog)
        self.btnSearch.setObjectName("btnSearch")
        self.gridLayout_2.addWidget(self.btnSearch, 1, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.lstSound, self.txtSound)
        Dialog.setTabOrder(self.txtSound, self.btnSearch)
        Dialog.setTabOrder(self.btnSearch, self.btnPlay)
        Dialog.setTabOrder(self.btnPlay, self.volumeSlider)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Sound Setup"))
        self.btnPlay.setText(_translate("Dialog", "Play"))
        self.label_2.setText(_translate("Dialog", "Sound-File:"))
        self.btnSearch.setText(_translate("Dialog", "..."))


