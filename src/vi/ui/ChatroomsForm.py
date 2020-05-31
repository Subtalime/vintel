# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ChatroomsForm.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(531, 421)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_11 = QtWidgets.QLabel(Form)
        self.label_11.setTextFormat(QtCore.Qt.PlainText)
        self.label_11.setWordWrap(True)
        self.label_11.setObjectName("label_11")
        self.verticalLayout.addWidget(self.label_11)
        self.txtChatrooms = QtWidgets.QPlainTextEdit(Form)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.txtChatrooms.setFont(font)
        self.txtChatrooms.setObjectName("txtChatrooms")
        self.verticalLayout.addWidget(self.txtChatrooms)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_11.setText(_translate("Form", "Enter the chatrooms to watch into the following field. Separate them by comma."))
