# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ChatroomsChooser.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(556, 197)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.roomnamesField = QtWidgets.QPlainTextEdit(Dialog)
        self.roomnamesField.setObjectName("roomnamesField")
        self.verticalLayout.addWidget(self.roomnamesField)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.defaultButton = QtWidgets.QPushButton(Dialog)
        self.defaultButton.setObjectName("defaultButton")
        self.horizontalLayout_2.addWidget(self.defaultButton)
        self.cancelButton = QtWidgets.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_2.addWidget(self.cancelButton)
        self.saveButton = QtWidgets.QPushButton(Dialog)
        self.saveButton.setObjectName("saveButton")
        self.horizontalLayout_2.addWidget(self.saveButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Chatrooms"))
        self.label.setText(_translate("Dialog", "Enter the chatrooms to watch into the following field. Separate them by comma."))
        self.defaultButton.setText(_translate("Dialog", "Restore Defaults"))
        self.cancelButton.setText(_translate("Dialog", "Cancel"))
        self.saveButton.setText(_translate("Dialog", "Save"))


