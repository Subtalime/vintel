#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
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

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QDialog
from .esiconfig import EsiConfig
from .esidialog import Ui_EsiDialog

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


class EsiConfigDialog(QDialog, Ui_EsiDialog):
    def __init__(self, esiConfig: EsiConfig, parent=None):
        QDialog.__init__(self, parent)
        self.esiConfig = esiConfig
        self.setupUi(self)
        self.setModal(True)
        self.textIntro.setText(PROMPT)
        self.checkBox.setChecked(False)
        self.checkBox.setEnabled(False)
        self.checkBox.stateChanged.connect(self.checkBoxState)
        self.txtClientId.setEnabled(True)
        self.txtClientId.setText(self.esiConfig.ESI_CLIENT_ID)
        if self.esiConfig.ESI_CLIENT_ID is not None:
            self.checkBox.setEnabled(True)
        self.txtClientId.textChanged.connect(self.txtClientIdState)
        self.txtCallback.setEnabled(True)
        self.txtCallback.setText(self.esiConfig.ESI_CALLBACK)
        self.txtCallback.textChanged.connect(self.txtCallbackState)
        self.txtCallback.setStyleSheet("QLineEdit{color: grey;}")
        self.txtSecretKey.setEnabled(False)
        if self.esiConfig.ESI_SECRET_KEY is not None:
            self.checkBox.setEnabled(True)
            self.checkBox.setChecked(True)
            self.txtSecretKey.setEnabled(True)
            self.txtSecretKey.setText(self.esiConfig.ESI_SECRET_KEY)
        self.cancelButton.clicked.connect(self.reject)
        self.okButton.setEnabled(False)
        self.okButton.clicked.connect(self.btnOk)

    def checkBoxState(self, state):
        self.txtSecretKey.setEnabled(state == Qt.Checked)

    def txtCallbackState(self):
        self.txtCallback.setStyleSheet("QLineEdit{color: black;}")

    def txtClientIdState(self):
        if len(self.txtClientId.text().strip()) >= 32:
            # self.checkBox.setEnabled(True)
            self.okButton.setEnabled(True)
        else:
            self.checkBox.setEnabled(False)
            self.okButton.setEnabled(False)

    def btnOk(self):
        callback = QUrl(self.txtCallback.text().strip())
        if callback.host() == "" or callback.port() == -1 or callback.path() == "":
            self.txtCallback.setFocus()
            return False
        self.esiConfig.ESI_CALLBACK = self.txtCallback.text().strip()
        self.esiConfig.ESI_CLIENT_ID = self.txtClientId.text().strip()
        if self.checkBox.isChecked():
            self.esiConfig.ESI_SECRET_KEY = self.txtSecretKey.text().strip()
        else:
            self.esiConfig.ESI_SECRET_KEY = None
        self.accept()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
