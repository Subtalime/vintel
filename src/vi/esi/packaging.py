#  Vintel - Visual Intel Chat Analyzer
#  Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
import logging, sys
from vi.cache.cache import Cache
from PyQt5.Qt import QCoreApplication
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLineEdit, \
    QCheckBox, QTextBrowser, QApplication, QDialogButtonBox, QStyle
from esiconfig import EsiConfig
from vi.resources import resourcePath
from vi.support.Intro import Ui_Dialog

introDialog = uic.loadUiType(resourcePath("Intro.ui"))[0]

PROMPT = """
<center><h3>This seems to be the first time you have started Vintel on this machine.</h3></center>
<hr/>
<p>To get access to ESI (EVE-Online Services Interface) you will need to create an application
under your EVE-Online account.<br />
Once you signed on to the EVE-API webpage at <a href="https://community.eveonline.com/">https://community.eveonline.com/</a>, 
create an Application (i.e. Vintel). 
<ul>
<li>Vintel does not require any special access to your account, so basic Access is sufficient with "Authentication Only"</li>
<li>For the Callback-URL enter "https://localhost:2020/callback/"</li>
<li>Click "Create Application" once you have confirmed the details.
</ul>
After you have created the Application, click on "View Application" and you will be presented with a Client-ID
and Secrect-Key. Use that Client-ID and fill in the field below.<br />
Vintel will try and authenticate with ESI using that Client-ID. ESI will then ask you
to authorize the access. Once you authorized, Vintel will store the Cookie received from
ESI so you wont have to authorize again. This Cookie received has an expiry-date but also contains
a Refresh-Token which will be attempted to be used once the Cookie has expired. Sometimes, even this
Refresh-Token will not be accepted and Vintel will direct you again to the Login-Page of EVE.
<br />
To reduce this behaviour, you can have Vintel store your Secret-Key (which you can see 
on your Application-Page at <a href="https://developers.eveonline.com/applications">https://developers.eveonline.com/applications</a>) in the local 
configuration file.</p>
"""


class StartupDialog(QDialog, introDialog, Ui_Dialog):
    def __init__(self, parent = None):
        super(__class__, self).__init__(parent)
        self.setupUi(self)
        self.textIntro.setText(PROMPT)
        self.checkBox.setChecked(False)
        self.checkBox.setEnabled(False)
        self.checkBox.stateChanged.connect(self.checkBoxState)
        self.txtClientId.setEnabled(True)
        self.txtClientId.textChanged.connect(self.txtClientIdState)
        self.txtCallback.setEnabled(True)
        self.txtCallback.textChanged.connect(self.txtCallbackState)
        self.txtCallback.setText(EsiConfig().ESI_CALLBACK)
        self.txtCallback.setStyleSheet("QLineEdit{color: grey;}")
        self.txtSecretKey.setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.buttonBox.accepted.connect(self.btnOk)
        self.buttonBox.rejected.connect(self.btnCancel)

    def checkBoxState(self, state):
        self.txtSecretKey.setEnabled(state == Qt.Checked)

    def txtCallbackState(self):
        pass

    def txtClientIdState(self):
        if len(self.txtClientId.text()) >= 32:
            self.checkBox.setEnabled(True)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.checkBox.setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def btnOk(self):
        self.accept()

    def btnCancel(self):
        self.reject()


class Packaging:
    def __init__(self, parent = None, testing: bool=False):
        self._testing = testing
        self.parent = parent

        pass

    def configureEsi(self) -> bool:
        # check for ESI-Client in the configuration
        # if it doesn't exist, prompt the user to create the Application
        # under his EVE Account and get him to enter the Client-ID.
        # Then modify esiconfig to store the Client-ID
        if EsiConfig().ESI_CLIENT_ID != "" and not self._testing:
            return True

        dialog = QDialog(parent=self.parent)
        dialog.setWindowTitle("Initial configuration for {}".format(EsiConfig.ESI_USER_AGENT))
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.okPressed)
        okButton.setDefault(True)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancelPressed)
        introText = QLineEdit()
        introText.setReadOnly(True)
        introText.setText(PROMPT)
        layout = QVBoxLayout()
        layout.addWidget(introText)
        layout.addWidget(okButton)
        layout.addWidget(cancelButton)
        dialog.setLayout(layout)
        dialog.show()
        dialog.exec_()

    def okPressed(self):
        pass

    def cancelPressed(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dia = StartupDialog(None)
    dia.show()
    dia.exec_()
    if dia.accepted:
        print(dia.txtClientId.text())
        print(dia.txtCallback.text())
        print(dia.txtSecretKey.text())
    sys.exit(app.exec_())
