# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'esidialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EsiDialog(object):
    def setupUi(self, EsiDialog):
        EsiDialog.setObjectName("EsiDialog")
        EsiDialog.resize(591, 429)
        self.verticalLayout = QtWidgets.QVBoxLayout(EsiDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.txtCallback = QtWidgets.QLineEdit(EsiDialog)
        self.txtCallback.setObjectName("txtCallback")
        self.gridLayout.addWidget(self.txtCallback, 2, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(EsiDialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.textIntro = QtWidgets.QTextEdit(EsiDialog)
        self.textIntro.setEnabled(False)
        self.textIntro.setFrameShape(QtWidgets.QFrame.Box)
        self.textIntro.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.textIntro.setObjectName("textIntro")
        self.gridLayout.addWidget(self.textIntro, 0, 0, 1, 3)
        self.label_2 = QtWidgets.QLabel(EsiDialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 4, 0, 1, 1)
        self.label = QtWidgets.QLabel(EsiDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.txtClientId = QtWidgets.QLineEdit(EsiDialog)
        self.txtClientId.setObjectName("txtClientId")
        self.gridLayout.addWidget(self.txtClientId, 1, 2, 1, 1)
        self.txtSecretKey = QtWidgets.QLineEdit(EsiDialog)
        self.txtSecretKey.setObjectName("txtSecretKey")
        self.gridLayout.addWidget(self.txtSecretKey, 4, 2, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(EsiDialog)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 3, 0, 1, 3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(300, -1, -1, -1)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cancelButton = QtWidgets.QPushButton(EsiDialog)
        self.cancelButton.setAutoDefault(False)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.okButton = QtWidgets.QPushButton(EsiDialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.gridLayout.addLayout(self.horizontalLayout, 5, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(EsiDialog)
        QtCore.QMetaObject.connectSlotsByName(EsiDialog)
        EsiDialog.setTabOrder(self.textIntro, self.txtClientId)
        EsiDialog.setTabOrder(self.txtClientId, self.txtCallback)
        EsiDialog.setTabOrder(self.txtCallback, self.checkBox)
        EsiDialog.setTabOrder(self.checkBox, self.txtSecretKey)
        EsiDialog.setTabOrder(self.txtSecretKey, self.cancelButton)
        EsiDialog.setTabOrder(self.cancelButton, self.okButton)

    def retranslateUi(self, EsiDialog):
        _translate = QtCore.QCoreApplication.translate
        EsiDialog.setWindowTitle(_translate("EsiDialog", "ESI Configuration"))
        self.label_3.setText(_translate("EsiDialog", "Callback URL:"))
        self.label_2.setText(_translate("EsiDialog", "Secret Key:"))
        self.label.setText(_translate("EsiDialog", "Client ID:"))
        self.checkBox.setText(_translate("EsiDialog", "store Secret Key"))
        self.cancelButton.setText(_translate("EsiDialog", "Cancel"))
        self.okButton.setText(_translate("EsiDialog", "OK"))
