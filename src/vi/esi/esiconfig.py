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
from vi.esi.esicache import EsiCache


class EsiConfig(six.with_metaclass(Singleton)):
    PROGNAME = "Vintel"

    # this will be set during authentication
    def setSecretKey(self, value: str):
        self.ESI_SECRET_KEY = value

    def getSecretKey(self):
        return self.ESI_SECRET_KEY

    # -----------------------------------------------------
    # ESI Configs
    # -----------------------------------------------------
    ESI_DATASOURCE = "tranquility"  # Change it to 'singularity' to use the test server
    ESI_SWAGGER_JSON = (
        "https://esi.tech.ccp.is/latest/swagger.json?datasource=%s" % ESI_DATASOURCE
    )
    # Run the Application, then register on "https://developers.eveonline.com/applications"
    # You will then receive your Secret and Client keys
    # ESI_CLIENT_ID = None  # your client ID
    ESI_USER_AGENT = PROGNAME

    def __init__(self, esi_cache: EsiCache = None):
        self.cache = esi_cache
        if self.cache is None:
            self.cache = EsiCache()

    @property
    def ESI_CLIENT_ID(self) -> str:
        return self.cache.get("esi_client_id", default="")

    @ESI_CLIENT_ID.setter
    def ESI_CLIENT_ID(self, value: str):
        self.cache.put("esi_client_id", value)

    @property
    def ESI_SECRET_KEY(self) -> str:
        return self.cache.get("esi_secret_key", default=None)

    @ESI_SECRET_KEY.setter
    def ESI_SECRET_KEY(self, value: str):
        self.cache.put("esi_secret_key", value)

    @property
    def HOST(self) -> str:
        # where the Webserver will be running
        return self.cache.get("esi_host", default="localhost")

    @HOST.setter
    def HOST(self, value: str):
        self.cache.put("esi_host", value)

    @property
    def PORT(self) -> int:
        # Local Call-Back Port
        return self.cache.get("esi_host_port", default=2020)

    @PORT.setter
    def PORT(self, value: int):
        self.cache.put("esi_host_port", value)

    @property
    def URI(self) -> str:
        # any http-path
        return self.cache.get("esi_host_uri", default="callback")

    @URI.setter
    def URI(self, value: str):
        self.cache.put("esi_host_uri", value)

    @property
    def ESI_CALLBACK(self) -> str:
        # the callback URI you gave CCP
        return self.cache.get("esi_call_back", default="http://%s:%d/%s" % (
            self.HOST,
            self.PORT,
            self.URI,
        ))

    @ESI_CALLBACK.setter
    def ESI_CALLBACK(self, value: str):
        self.cache.put("esi_call_back", value)

    @property
    def ESI_TOKEN(self) -> list:
        return self.cache.get("esi_tokens")

    @ESI_TOKEN.setter
    def ESI_TOKEN(self, value: list):
        self.cache.put("esi_tokens", value)
