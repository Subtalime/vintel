#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2021. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#

import sys
import logging
import webbrowser
from esipy import EsiClient, EsiSecurity
from esipy.security import APIException
from esipy.utils import generate_code_verifier

from vi.esi.esiconfigdialog import EsiConfigDialog, EsiConfig
from vi.esi.esiwait import EsiWait


class EsiLogin:
    """This is intended to create a Login-Sequence to EVE Application-Authorisation
    currently it's not being used, since Vintel does not require any secure values from the Client
    """
    def __init__(self):
        self.LOGGER = logging.getLogger(__name__)
        self.esi_config = EsiConfig()
        self.headers = {
                "User-Agent": "{} Intel Management Tool".format(
                    self.esi_config.PROGNAME
                ),
            }

    def get_security(self):
        if not self.esi_config.ESI_CLIENT_ID:
            # TODO: look at PyFa to see how they do it...
            # TODO: until then, we should stop storing the SecretKey
            with EsiConfigDialog(self.esi_config) as inputDia:
                res = inputDia.exec_()
                if not res == inputDia.Accepted:
                    self.LOGGER.info("User canceled Client-ID Input-Dialog")
                    sys.exit(-1)
        secure = EsiSecurity(
            # The application (matching ESI_CLIENT_ID) must have the same Callback configured!
            redirect_uri=self.esi_config.ESI_CALLBACK,
            client_id=self.esi_config.ESI_CLIENT_ID,
            code_verifier=generate_code_verifier(),
            headers=self.headers,
        )
        # this authentication can be used with all ESI calls
        self.esiClient = EsiClient(
            security=secure,
            retry_requests=True,
            headers=self.headers
        )
        self.apiInfo = None
        self.esiApp = None
        refreshKey = None
        if self.esi_config.ESI_TOKEN:
            refreshKey = self.esi_config.ESI_TOKEN["refresh_token"]
        while not self.apiInfo:
            try:
                if self.esi_config.ESI_SECRET_KEY:
                    self.LOGGER.debug("Checking the Secretkey")
                    self.waitForSecretKey()
                    tokens = secure.auth(self.esi_config.ESI_SECRET_KEY)
                    self.esi_config.ESI_SECRET_KEY = None
                    self.apiInfo = secure.verify()
                    # store the Token
                    self.esi_config.ESI_TOKEN = tokens
                    # self.esicache.set("esi_token", self.tokens)
                    self.LOGGER.debug("Secretkey success")
                elif refreshKey:
                    self.LOGGER.debug("Checking the Refresh-Token")
                    secure.update_token(
                        {
                            "access_token": "",
                            "expires_in": -1,
                            "refresh_token": refreshKey,
                        }
                    )
                    refreshKey = None
                    try:
                        self.apiInfo = secure.refresh()
                    except:
                        self.esi_config.ESI_TOKEN = None
                        # self.esicache.delete("esi_token")
                        continue
                    self.LOGGER.debug("Refreshtoken success")
                elif self.esi_config.ESI_TOKEN:
                    self.LOGGER.debug("Checking the Tokenkey")
                    secure.update_token(self.esi_config.ESI_TOKEN)
                    tokenKey = None
                    try:
                        self.apiInfo = secure.refresh()
                    except:
                        self.esi_config.ESI_TOKEN = None
                        # self.esicache.delete("esi_token")
                        continue
                    self.LOGGER.debug("Tokenkey success")
                else:
                    self.LOGGER.debug("Waiting for Website response of Secretkey")
                    self.waitForSecretKey()
            except APIException as e:
                self.LOGGER.error("EsiAPI Error", e)
                APIException("Problem with the API?", e)
                self.waitForSecretKey()
            except AttributeError as e:
                self.LOGGER.error("EsiAttribute Error", e)
                APIException("Attribute problem?", e)
                self.waitForSecretKey()
            except Exception as e:
                self.LOGGER.error("Some unexpected error in Esi", e)
                sys.exit(-1)

    def waitForSecretKey(self):
        # Take the user to the EVE-Auth page in a Browser-Window
        ssoUri = self.security.get_auth_uri(
            state="Authentication for {}".format(self.esiConfig.PROGNAME),
            # scopes=['get_universe_system_jumps']
        )
        webbrowser.open(ssoUri)
        # Wait for the user to complete login or cancel
        wait_dialog = EsiWait()
        wait_dialog.exec_()
        # User decided to cancel the operation
        if not self.esiConfig.ESI_SECRET_KEY:
            sys.exit(-1)


