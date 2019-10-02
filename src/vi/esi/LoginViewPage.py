from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import pyqtSignal, QPointF, QUrl
from esipy import EsiSecurity
from vi.esi.esi import generate_token


class LoginView(QWebEnginePage):
    def __init__(self, parent: 'QObject'=None):
        super().__init__(parent)
        self.channel = QWebChannel()

        self.esiSec = EsiSecurity()
        redirectUrl = self.esiSec.get_auth_uri(
            state=generate_token(),
            scopes=['']
            # scopes=['esi-wallet.read_character_wallet.v1']
        )
