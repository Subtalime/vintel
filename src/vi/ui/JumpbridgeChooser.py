# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'JumpbridgeChooser.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(696, 394)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setObjectName("widget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox = QtWidgets.QGroupBox(self.widget)
        self.groupBox.setEnabled(True)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.urlField = QtWidgets.QLineEdit(self.groupBox)
        self.urlField.setObjectName("urlField")
        self.verticalLayout_2.addWidget(self.urlField)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.label2 = QtWidgets.QLabel(self.groupBox)
        self.label2.setObjectName("label2")
        self.verticalLayout.addWidget(self.label2)
        self.clipboardButton = QtWidgets.QPushButton(self.groupBox)
        self.clipboardButton.setEnabled(True)
        self.clipboardButton.setObjectName("clipboardButton")
        self.verticalLayout.addWidget(self.clipboardButton)
        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.widget)
        self.widget2 = QtWidgets.QWidget(Dialog)
        self.widget2.setObjectName("widget2")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.widget2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.groupBox2 = QtWidgets.QGroupBox(self.widget2)
        self.groupBox2.setObjectName("groupBox2")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox2)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.formatInfoField = QtWidgets.QTextEdit(self.groupBox2)
        self.formatInfoField.setStyleSheet("background-color: rgb(217, 217, 217);")
        self.formatInfoField.setReadOnly(True)
        self.formatInfoField.setObjectName("formatInfoField")
        self.gridLayout_5.addWidget(self.formatInfoField, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox2, 0, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.widget2)
        self.widget3 = QtWidgets.QWidget(Dialog)
        self.widget3.setObjectName("widget3")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget3)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.cancelButton = QtWidgets.QPushButton(self.widget3)
        self.cancelButton.setAutoDefault(False)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_4.addWidget(self.cancelButton)
        self.saveButton = QtWidgets.QPushButton(self.widget3)
        self.saveButton.setObjectName("saveButton")
        self.horizontalLayout_4.addWidget(self.saveButton)
        self.verticalLayout_3.addWidget(self.widget3)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Jumpbridge Data"))
        self.groupBox.setTitle(_translate("Dialog", "Path to the Data"))
        self.label.setText(_translate("Dialog", "Please enter the URL to the Jumpbridge data:"))
        self.label2.setText(_translate("Dialog", "For example: http://example.org/jumpbridge_data.txt"))
        self.clipboardButton.setText(_translate("Dialog", "Paste Clipboard"))
        self.groupBox2.setTitle(_translate("Dialog", "Format of the jumpbridge data:"))
        self.cancelButton.setText(_translate("Dialog", "Cancel"))
        self.saveButton.setText(_translate("Dialog", "Save"))


