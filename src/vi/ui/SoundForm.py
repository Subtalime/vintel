# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SoundForm.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(676, 411)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.lstSound = QtWidgets.QTableView(Form)
        self.lstSound.setObjectName("lstSound")
        self.verticalLayout_2.addWidget(self.lstSound)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnPlay = QtWidgets.QPushButton(Form)
        self.btnPlay.setObjectName("btnPlay")
        self.horizontalLayout.addWidget(self.btnPlay)
        self.sliderVolume = QtWidgets.QSlider(Form)
        self.sliderVolume.setOrientation(QtCore.Qt.Horizontal)
        self.sliderVolume.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.sliderVolume.setObjectName("sliderVolume")
        self.horizontalLayout.addWidget(self.sliderVolume)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)
        self.txtSound = QtWidgets.QLineEdit(Form)
        self.txtSound.setObjectName("txtSound")
        self.gridLayout.addWidget(self.txtSound, 0, 1, 1, 1)
        self.label_8 = QtWidgets.QLabel(Form)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 0, 0, 1, 1)
        self.btnSoundSearch = QtWidgets.QPushButton(Form)
        self.btnSoundSearch.setObjectName("btnSoundSearch")
        self.gridLayout.addWidget(self.btnSoundSearch, 0, 2, 1, 1)
        self.horizontalLayout_2.addLayout(self.gridLayout)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.lstSound, self.btnPlay)
        Form.setTabOrder(self.btnPlay, self.sliderVolume)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.btnPlay.setText(_translate("Form", "Play"))
        self.label_8.setText(_translate("Form", "Sound File:"))
        self.btnSoundSearch.setText(_translate("Form", "..."))
