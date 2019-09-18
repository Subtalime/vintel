# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SoundSetup.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(247, 300)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setObjectName("widget")
        self.testSoundButton = QtWidgets.QPushButton(self.widget)
        self.testSoundButton.setGeometry(QtCore.QRect(10, 30, 103, 26))
        self.testSoundButton.setObjectName("testSoundButton")
        self.testSoundButton.setEnabled(True)
        self.closeButton = QtWidgets.QPushButton(self.widget)
        self.closeButton.setGeometry(QtCore.QRect(10, 240, 103, 26))
        self.closeButton.setObjectName("closeButton")
        self.horizontalLayout.addWidget(self.widget)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.volumeSlider = QtWidgets.QSlider(Dialog)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setTracking(False)
        self.volumeSlider.setOrientation(QtCore.Qt.Vertical)
        self.volumeSlider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.volumeSlider.setObjectName("volumeSlider")
        self.gridLayout.addWidget(self.volumeSlider, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.stopSoundButton.setEnabled(False)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Sound Setup"))
        self.testSoundButton.setText(_translate("Dialog", "Testsound"))
        self.closeButton.setText(_translate("Dialog", "Close"))
        self.label.setText(_translate("Dialog", "Volume"))


