#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
import six
from vi.singleton import Singleton


class EsiConfig(six.with_metaclass(Singleton)):
    PROGNAME = "Vintel"

    # this will be set during authentication
    def setSecretKey(self, value: str):
        self.ESI_SECRET_KEY = value
    def getSecretKey(self):
        return self.ESI_SECRET_KEY

    # Local Call-Back Port
    PORT = 2020
    # where the Webserver will be running
    HOST = 'localhost'
    # any http-path
    URI = 'callback'

    # -----------------------------------------------------
    # ESI Configs
    # -----------------------------------------------------
    ESI_DATASOURCE = 'tranquility'  # Change it to 'singularity' to use the test server
    ESI_SWAGGER_JSON = 'https://esi.tech.ccp.is/latest/swagger.json?datasource=%s' % ESI_DATASOURCE
    # Run the Application, then register on "https://developers.eveonline.com/applications"
    # You will then receive your Secret and Client keys
    ESI_CLIENT_ID = None  # your client ID
    # ESI_CLIENT_ID = '0ab476e584064214869d532acd027494'  # your client ID example
    # ESI_CLIENT_ID = '50de89684c374189a25ccf83aa1d928a'  # your client ID example
    # This ESI_SECRET_KEY is currently not being used...
    # ESI_SECRET_KEY = "mh9DMVZfdPVTtwq6btOA1I4OblUqcWuaSEWzoaN4"
#    ESI_SECRET_KEY = "QUD3IsBSMa3AtEHHDMBhsTZsurL8s8FrauQoOF7f"
    ESI_SECRET_KEY = ""
    ESI_CALLBACK = 'http://%s:%d/%s' % (HOST, PORT, URI)  # the callback URI you gave CCP
    ESI_USER_AGENT = PROGNAME
