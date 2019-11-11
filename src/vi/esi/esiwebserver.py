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
import logging
from urllib import parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from PyQt5.QtCore import QUrl
from .esiconfig import EsiConfig

LOGGER = logging.getLogger(__name__)


class EsiWebServer(object):
    def __init__(self):
        hostString = QUrl(EsiConfig.ESI_CALLBACK)
        self.httpd = HTTPServer((hostString.host(), hostString.port()),
                                self.EsiHTTPRequestHandler)
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True

    def start(self):
        self.server_thread.start()

    def stop(self):
        if self.server_thread.isAlive():
            self.httpd.shutdown()
        self.httpd.server_close()

    class EsiHTTPRequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            try:
                thisquery = parse.parse_qs(parse.urlsplit(self.requestline).query)
                if thisquery['code']:
                    # store temporary Secretkey
                    EsiConfig.ESI_SECRET_KEY = thisquery['code'][0]
                    self.wfile.write(
                        b"You have verified your account on ESI. You can now close this window")

            except Exception as e:
                LOGGER.error("Unexpected response: %s: %r", self.requestline, e)
                self.wfile.write(b"I don't know what you are on about")
