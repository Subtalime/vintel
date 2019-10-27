# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ShipDialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(415, 300)
        self.lblShipName = QtWidgets.QLabel(Dialog)
        self.lblShipName.setGeometry(QtCore.QRect(0, 0, 401, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.lblShipName.setFont(font)
        self.lblShipName.setObjectName("lblShipName")
        self.graphShip = QtWidgets.QGraphicsView(Dialog)
        self.graphShip.setGeometry(QtCore.QRect(0, 40, 241, 221))
        self.graphShip.setObjectName("graphShip")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Ship"))
        self.lblShipName.setText(_translate("Dialog", "TextLabel"))
