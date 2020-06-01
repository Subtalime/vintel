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
import threading
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QDialog
from .esiconfig import EsiConfig
from .esiwaitdialog import Ui_EsiWaitDialog
from .esiwebserver import EsiWebServer


class EsiWait(QDialog, Ui_EsiWaitDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.waiter = WaitThread()
        self.waiter_thread = threading.Thread(target=self.waiter.wait_for_secret)
        self.waiter_thread.daemon = True
        self.waiter.secret_received.connect(self.received)
        self.buttonCancel.clicked.connect(self.cancel_request)
        self.server = EsiWebServer()

    def show(self):
        if not self.waiter_thread.isAlive():
            self.waiter_thread.start()
            self.server.start()
        super().show()

    def exec_(self):
        # if not self.waiter_thread.isAlive():
        self.waiter_thread.start()
        self.server.start()
        QDialog.exec_(self)

    def cancel_request(self):
        self.server.stop()
        self.reject()
        self.hide()

    def received(self, secret):
        self.server.stop()
        self.accept()
        self.hide()


class WaitThread(QObject):
    secret_received = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)
        self.__is_shut_down = threading.Event()
        self.__shutdown_request = False
        EsiConfig().ESI_SECRET_KEY = None

    def wait_for_secret(self, poll_interval: float = 0.5):
        self.__is_shut_down.clear()
        import time

        try:
            while not EsiConfig().ESI_SECRET_KEY and not self.__shutdown_request:
                time.sleep(poll_interval)
        finally:
            if not self.__shutdown_request:
                self.secret_received.emit(EsiConfig().ESI_SECRET_KEY)
            self.__shutdown_request = False
            self.__is_shut_down.set()

    def shutdown(self):
        self.__shutdown_request = True
        self.__is_shut_down.wait()
