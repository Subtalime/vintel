# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GeneralForm.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(680, 403)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox_3 = QtWidgets.QGroupBox(Form)
        self.groupBox_3.setFlat(True)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.groupBox_6 = QtWidgets.QGroupBox(self.groupBox_3)
        self.groupBox_6.setFlat(True)
        self.groupBox_6.setObjectName("groupBox_6")
        self.gridLayout_10 = QtWidgets.QGridLayout(self.groupBox_6)
        self.gridLayout_10.setObjectName("gridLayout_10")
        self.label_20 = QtWidgets.QLabel(self.groupBox_6)
        self.label_20.setObjectName("label_20")
        self.gridLayout_10.addWidget(self.label_20, 0, 0, 1, 1)
        self.label_21 = QtWidgets.QLabel(self.groupBox_6)
        self.label_21.setObjectName("label_21")
        self.gridLayout_10.addWidget(self.label_21, 1, 0, 1, 1)
        self.txtMessageExpiry = QtWidgets.QLineEdit(self.groupBox_6)
        self.txtMessageExpiry.setObjectName("txtMessageExpiry")
        self.gridLayout_10.addWidget(self.txtMessageExpiry, 0, 1, 1, 1)
        self.txtKosInterval = QtWidgets.QLineEdit(self.groupBox_6)
        self.txtKosInterval.setObjectName("txtKosInterval")
        self.gridLayout_10.addWidget(self.txtKosInterval, 1, 1, 1, 1)
        self.gridLayout_9.addWidget(self.groupBox_6, 2, 1, 1, 1)
        self.checkScanCharacter = QtWidgets.QCheckBox(self.groupBox_3)
        self.checkScanCharacter.setObjectName("checkScanCharacter")
        self.gridLayout_9.addWidget(self.checkScanCharacter, 0, 2, 1, 1)
        self.checkShipNames = QtWidgets.QCheckBox(self.groupBox_3)
        self.checkShipNames.setObjectName("checkShipNames")
        self.gridLayout_9.addWidget(self.checkShipNames, 1, 2, 1, 1)
        self.label_19 = QtWidgets.QLabel(self.groupBox_3)
        self.label_19.setObjectName("label_19")
        self.gridLayout_9.addWidget(self.label_19, 1, 1, 1, 1)
        self.label_18 = QtWidgets.QLabel(self.groupBox_3)
        self.label_18.setObjectName("label_18")
        self.gridLayout_9.addWidget(self.label_18, 0, 1, 1, 1)
        self.horizontalLayout.addWidget(self.groupBox_3)
        self.groupBox_5 = QtWidgets.QGroupBox(Form)
        self.groupBox_5.setToolTip("")
        self.groupBox_5.setFlat(True)
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.groupBox_5)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.checkNotifyOwn = QtWidgets.QCheckBox(self.groupBox_5)
        self.checkNotifyOwn.setObjectName("checkNotifyOwn")
        self.gridLayout_8.addWidget(self.checkNotifyOwn, 1, 1, 1, 1)
        self.btnColor = QtWidgets.QPushButton(self.groupBox_5)
        self.btnColor.setObjectName("btnColor")
        self.gridLayout_8.addWidget(self.btnColor, 5, 1, 1, 1)
        self.txtJumpDistance = QtWidgets.QLineEdit(self.groupBox_5)
        self.txtJumpDistance.setMaxLength(1)
        self.txtJumpDistance.setObjectName("txtJumpDistance")
        self.gridLayout_8.addWidget(self.txtJumpDistance, 4, 1, 1, 1)
        self.label_15 = QtWidgets.QLabel(self.groupBox_5)
        self.label_15.setObjectName("label_15")
        self.gridLayout_8.addWidget(self.label_15, 1, 0, 1, 1)
        self.checkPopupNotification = QtWidgets.QCheckBox(self.groupBox_5)
        self.checkPopupNotification.setObjectName("checkPopupNotification")
        self.gridLayout_8.addWidget(self.checkPopupNotification, 2, 1, 1, 1)
        self.label_17 = QtWidgets.QLabel(self.groupBox_5)
        self.label_17.setObjectName("label_17")
        self.gridLayout_8.addWidget(self.label_17, 5, 0, 1, 1)
        self.label_16 = QtWidgets.QLabel(self.groupBox_5)
        self.label_16.setObjectName("label_16")
        self.gridLayout_8.addWidget(self.label_16, 4, 0, 1, 1)
        self.label_14 = QtWidgets.QLabel(self.groupBox_5)
        self.label_14.setObjectName("label_14")
        self.gridLayout_8.addWidget(self.label_14, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox_5)
        self.label.setObjectName("label")
        self.gridLayout_8.addWidget(self.label, 3, 0, 1, 1)
        self.cmbLogLevel = QtWidgets.QComboBox(self.groupBox_5)
        self.cmbLogLevel.setObjectName("cmbLogLevel")
        self.gridLayout_8.addWidget(self.cmbLogLevel, 3, 1, 1, 1)
        self.horizontalLayout.addWidget(self.groupBox_5)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_3.setTitle(_translate("Form", "Chat-Messages"))
        self.groupBox_6.setTitle(_translate("Form", "in Seconds"))
        self.label_20.setText(_translate("Form", "Message expiry :"))
        self.label_21.setText(_translate("Form", "KOS Clipboard interval:"))
        self.txtMessageExpiry.setToolTip(
            _translate("Form", "how long to keep messages in the Chat-History")
        )
        self.checkScanCharacter.setToolTip(
            _translate(
                "Form",
                "scan messages for Character-Names and provide a link to zKillboard",
            )
        )
        self.checkScanCharacter.setText(_translate("Form", "enable"))
        self.checkShipNames.setToolTip(
            _translate(
                "Form",
                "analyse Chat-Messages for Ship-Names and provide a link to zKillboard",
            )
        )
        self.checkShipNames.setText(_translate("Form", "enable"))
        self.label_19.setText(_translate("Form", "Scan for Ship-Names"))
        self.label_18.setText(_translate("Form", "Scan for Character-Names:"))
        self.groupBox_5.setTitle(_translate("Form", "Other"))
        self.checkNotifyOwn.setToolTip(
            _translate(
                "Form",
                "should an Alert be raised for you if your own Character enters it in a Chat-Room",
            )
        )
        self.checkNotifyOwn.setText(_translate("Form", "enabled"))
        self.btnColor.setToolTip(
            _translate(
                "Form", "change background color of all Windows (may require restart)"
            )
        )
        self.btnColor.setText(_translate("Form", "Color..."))
        self.txtJumpDistance.setToolTip(
            _translate(
                "Form",
                "How many systems away should the messages be scanned for, before being alerted",
            )
        )
        self.label_15.setText(_translate("Form", "Notify on own Message/Alert:"))
        self.checkPopupNotification.setToolTip(
            _translate(
                "Form", "Pop-Up the Tray-Icon with a brief notification about an Alert"
            )
        )
        self.checkPopupNotification.setText(_translate("Form", "enabled"))
        self.label_17.setText(_translate("Form", "Window Background Color :"))
        self.label_16.setText(_translate("Form", "Jump-Distance-Alert:"))
        self.label_14.setText(_translate("Form", "Pop-Up Tray-Icon on Alert:"))
        self.label.setText(_translate("Form", "Log-Level:"))
        self.cmbLogLevel.setToolTip(
            _translate("Form", "set the default Logging-Level for the configured Logs")
        )
