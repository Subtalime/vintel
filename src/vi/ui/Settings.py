# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Settings.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(679, 423)
        Dialog.setSizeGripEnabled(True)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.widget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.groupBox = QtWidgets.QGroupBox(self.tab_1)
        self.groupBox.setGeometry(QtCore.QRect(0, 10, 270, 79))
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout_3.addWidget(self.label, 0, 0, 1, 1)
        self.txtMessageExpiry = QtWidgets.QLineEdit(self.groupBox)
        self.txtMessageExpiry.setObjectName("txtMessageExpiry")
        self.gridLayout_3.addWidget(self.txtMessageExpiry, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout_3.addWidget(self.label_2, 1, 0, 1, 1)
        self.txtKosInterval = QtWidgets.QLineEdit(self.groupBox)
        self.txtKosInterval.setObjectName("txtKosInterval")
        self.gridLayout_3.addWidget(self.txtKosInterval, 1, 1, 1, 1)
        self.frame = QtWidgets.QFrame(self.tab_1)
        self.frame.setGeometry(QtCore.QRect(10, 280, 611, 43))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.formLayout_2 = QtWidgets.QFormLayout(self.frame)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_4 = QtWidgets.QLabel(self.frame)
        self.label_4.setObjectName("label_4")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.btnColor = QtWidgets.QPushButton(self.frame)
        self.btnColor.setObjectName("btnColor")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.btnColor)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_1)
        self.groupBox_2.setGeometry(QtCore.QRect(310, 10, 231, 81))
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        self.checkScanCharacter = QtWidgets.QCheckBox(self.groupBox_2)
        self.checkScanCharacter.setObjectName("checkScanCharacter")
        self.gridLayout_2.addWidget(self.checkScanCharacter, 0, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 1, 0, 1, 1)
        self.checkShipNames = QtWidgets.QCheckBox(self.groupBox_2)
        self.checkShipNames.setObjectName("checkShipNames")
        self.gridLayout_2.addWidget(self.checkShipNames, 1, 1, 1, 1)
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab_1)
        self.groupBox_4.setGeometry(QtCore.QRect(0, 110, 391, 91))
        self.groupBox_4.setFlat(True)
        self.groupBox_4.setObjectName("groupBox_4")
        self.label_6 = QtWidgets.QLabel(self.groupBox_4)
        self.label_6.setGeometry(QtCore.QRect(10, 20, 141, 16))
        self.label_6.setObjectName("label_6")
        self.checkNotifyOwn = QtWidgets.QCheckBox(self.groupBox_4)
        self.checkNotifyOwn.setGeometry(QtCore.QRect(140, 20, 70, 17))
        self.checkNotifyOwn.setObjectName("checkNotifyOwn")
        self.checkPopupNotification = QtWidgets.QCheckBox(self.groupBox_4)
        self.checkPopupNotification.setGeometry(QtCore.QRect(140, 50, 70, 17))
        self.checkPopupNotification.setObjectName("checkPopupNotification")
        self.label_7 = QtWidgets.QLabel(self.groupBox_4)
        self.label_7.setGeometry(QtCore.QRect(10, 50, 121, 16))
        self.label_7.setObjectName("label_7")
        self.tabWidget.addTab(self.tab_1, "")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 10, 611, 280))
        self.groupBox_3.setFlat(True)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.cmbAlertType = QtWidgets.QComboBox(self.groupBox_3)
        self.cmbAlertType.setObjectName("cmbAlertType")
        self.gridLayout_4.addWidget(self.cmbAlertType, 0, 0, 1, 1)
        self.tableViewMap = QtWidgets.QTableView(self.groupBox_3)
        self.tableViewMap.setObjectName("tableViewMap")
        self.gridLayout_4.addWidget(self.tableViewMap, 1, 0, 1, 2)
        self.pbMapAddTime = QtWidgets.QPushButton(self.groupBox_3)
        self.pbMapAddTime.setObjectName("pbMapAddTime")
        self.gridLayout_4.addWidget(self.pbMapAddTime, 2, 0, 1, 1)
        self.pbMapDelTime = QtWidgets.QPushButton(self.groupBox_3)
        self.pbMapDelTime.setObjectName("pbMapDelTime")
        self.gridLayout_4.addWidget(self.pbMapDelTime, 2, 1, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.widget)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.gridLayout.addWidget(self.widget, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "in Seconds"))
        self.label.setText(_translate("Dialog", "Message expiry :"))
        self.label_2.setText(_translate("Dialog", "KOS Clipboard interval:"))
        self.label_4.setText(_translate("Dialog", "Window Background Color :"))
        self.btnColor.setText(_translate("Dialog", "Color..."))
        self.groupBox_2.setTitle(_translate("Dialog", "Chat-Filter"))
        self.label_3.setText(_translate("Dialog", "Scan for Character-Names:"))
        self.checkScanCharacter.setText(_translate("Dialog", "enable"))
        self.label_5.setText(_translate("Dialog", "Scan for Ship-Names"))
        self.checkShipNames.setText(_translate("Dialog", "enable"))
        self.groupBox_4.setTitle(_translate("Dialog", "Other"))
        self.label_6.setText(_translate("Dialog", "Notify on own Message:"))
        self.checkNotifyOwn.setText(_translate("Dialog", "enabled"))
        self.checkPopupNotification.setText(_translate("Dialog", "enabled"))
        self.label_7.setText(_translate("Dialog", "Pop-Up notification:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("Dialog", "General"))
        self.groupBox_3.setTitle(_translate("Dialog", "Alert Settings"))
        self.pbMapAddTime.setText(_translate("Dialog", "add Time"))
        self.pbMapDelTime.setText(_translate("Dialog", "delete Time"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Dialog", "Map-Display"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Dialog", "Sound"))
