# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ChatEntry.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(86, 46)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setContentsMargins(2, 2, 2, 2)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.avatarLabel = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.avatarLabel.sizePolicy().hasHeightForWidth())
        self.avatarLabel.setSizePolicy(sizePolicy)
        self.avatarLabel.setMinimumSize(QtCore.QSize(32, 32))
        self.avatarLabel.setMaximumSize(QtCore.QSize(32, 32))
        self.avatarLabel.setTextFormat(QtCore.Qt.RichText)
        self.avatarLabel.setScaledContents(True)
        self.avatarLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.avatarLabel.setObjectName("avatarLabel")
        self.horizontalLayout.addWidget(self.avatarLabel)
        self.textLabel = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel.sizePolicy().hasHeightForWidth())
        self.textLabel.setSizePolicy(sizePolicy)
        self.textLabel.setTextFormat(QtCore.Qt.RichText)
        self.textLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.textLabel.setWordWrap(True)
        self.textLabel.setObjectName("textLabel")
        self.horizontalLayout.addWidget(self.textLabel)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 1, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.avatarLabel.setText(_translate("Form", "TextLabel"))
        self.textLabel.setText(_translate("Form", "?"))


