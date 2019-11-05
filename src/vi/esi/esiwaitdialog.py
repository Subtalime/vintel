# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'esiwaitdialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets


class Ui_EsiWaitDialog(object):
    def setupUi(self, EsiWaitDialog):
        EsiWaitDialog.setObjectName("EsiWaitDialog")
        EsiWaitDialog.resize(291, 108)
        self.label = QtWidgets.QLabel(EsiWaitDialog)
        self.label.setGeometry(QtCore.QRect(20, 30, 239, 16))
        self.label.setObjectName("label")
        self.buttonCancel = QtWidgets.QPushButton(EsiWaitDialog)
        self.buttonCancel.setGeometry(QtCore.QRect(110, 70, 75, 23))
        self.buttonCancel.setDefault(True)
        self.buttonCancel.setObjectName("buttonCancel")

        self.retranslateUi(EsiWaitDialog)
        QtCore.QMetaObject.connectSlotsByName(EsiWaitDialog)

    def retranslateUi(self, EsiWaitDialog):
        _translate = QtCore.QCoreApplication.translate
        EsiWaitDialog.setWindowTitle(_translate("EsiWaitDialog", "Web-Server-Response"))
        self.label.setText(_translate("EsiWaitDialog", "Waiting for user to complete EVE-Authorization..."))
        self.buttonCancel.setText(_translate("EsiWaitDialog", "Cancel ..."))


