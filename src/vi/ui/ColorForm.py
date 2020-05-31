# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ColorForm.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(655, 272)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.colorType = QtWidgets.QComboBox(Form)
        self.colorType.setObjectName("colorType")
        self.horizontalLayout_2.addWidget(self.colorType)
        self.label_12 = QtWidgets.QLabel(Form)
        self.label_12.setAlignment(QtCore.Qt.AlignCenter)
        self.label_12.setWordWrap(True)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_2.addWidget(self.label_12)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.colorTable = QtWidgets.QTableView(Form)
        self.colorTable.setObjectName("colorTable")
        self.verticalLayout.addWidget(self.colorTable)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.colorDelTime = QtWidgets.QPushButton(Form)
        self.colorDelTime.setObjectName("colorDelTime")
        self.horizontalLayout.addWidget(self.colorDelTime)
        self.colorAddTime = QtWidgets.QPushButton(Form)
        self.colorAddTime.setObjectName("colorAddTime")
        self.horizontalLayout.addWidget(self.colorAddTime)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.colorType, self.colorDelTime)
        Form.setTabOrder(self.colorDelTime, self.colorAddTime)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_12.setText(_translate("Form", "Background-Colors will blend over from the lowest timeline to the next highest and end up in WHITE"))
        self.colorDelTime.setText(_translate("Form", "delete Time"))
        self.colorAddTime.setText(_translate("Form", "add Time"))
