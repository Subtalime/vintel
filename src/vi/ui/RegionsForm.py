# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RegionsForm.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(817, 398)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_10 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_10.setFont(font)
        self.label_10.setTextFormat(QtCore.Qt.PlainText)
        self.label_10.setWordWrap(True)
        self.label_10.setObjectName("label_10")
        self.verticalLayout.addWidget(self.label_10)
        self.listRegion = QtWidgets.QListWidget(Form)
        self.listRegion.setAlternatingRowColors(False)
        self.listRegion.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.listRegion.setSelectionRectVisible(True)
        self.listRegion.setObjectName("listRegion")
        self.verticalLayout.addWidget(self.listRegion)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_9 = QtWidgets.QLabel(Form)
        self.label_9.setObjectName("label_9")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_9)
        self.txtRegions = QtWidgets.QLineEdit(Form)
        self.txtRegions.setObjectName("txtRegions")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.txtRegions)
        self.verticalLayout_2.addLayout(self.formLayout)
        self.btnRegionHelp = QtWidgets.QPushButton(Form)
        self.btnRegionHelp.setObjectName("btnRegionHelp")
        self.verticalLayout_2.addWidget(self.btnRegionHelp)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_10.setText(
            _translate("Form", "Select the regions to keep on the watch list:")
        )
        self.listRegion.setSortingEnabled(True)
        self.label_9.setText(_translate("Form", "Region-Files (comma separated):"))
        self.btnRegionHelp.setText(_translate("Form", "Help me on this..."))
