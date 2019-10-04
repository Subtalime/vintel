import logging
from esipy.utils import generate_code_verifier
from esipy import EsiClient, EsiApp, EsiSecurity
from esiconfig import EsiConfig
import vi.version


class EsiInterface:

    def __init__(self):
        logging.debug("Creating ESI access")
        self.authenticated = False
        self.headers = {'User-Agent': "{} Intel Management Tool".format(vi.version.PROGNAME)}
        self.codeverifier = generate_code_verifier()
        try:
            # this uses PKCE (pixie) authorisation with ESI
            self.security = EsiSecurity(
                # The application (matching ESI_CLIENT_ID) must have the same Callback configured!
                redirect_uri=EsiConfig().ESI_CALLBACK,
                client_id=EsiConfig().ESI_CLIENT_ID,
                code_verifier= self.codeverifier,
                headers=self.headers
            )
            ssoUri = self.security.get_auth_uri(state="Authentication for {}".format(vi.version.PROGNAME),
                                                scopes=None
                                                )

            # this authentication can be used with all ESI calls
            self.esiClient = EsiClient(security=self.security,
                                       retry_requests=True,
                                       headers=self.headers
                                       )
            logging.debug("ESI loading Swagger...")
            self.esiApp = EsiApp().get_latest_swagger
            logging.debug("ESI loading Swagger...complete")
            # self.apiInfo = self.security.verify()
            self.authenticated = True
            logging.debug("Finished authorizing with ESI (using PKCE)")
        except Exception as e:
            logging.critical("Error authenticating with ESI", e)
            exit(-1)

    def getCharacter(self, charid: int):
        response = None
        try:
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_characters_character_id'] (character_id=charid)
                response = self.esiClient.request(op)
                return response.data
        except Exception as e:
            logging.error("Error retrieving Character {} from ESI".format(charid), e)
        return None

    def getCorporation(self, corpid: int):
        response = None
        try:
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_corporations_corporation_id'] (character_id=corpid)
                response = self.esiClient.request(op)
                return response.data
        except Exception as e:
            logging.error("Error retrieving Corporation {} from ESI".format(corpid), e)
        return None

    def getCorporationHistory(self, charid: int):
        response = None
        try:
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_characters_character_id_corporationhistory'] (character_id=charid)
                response = self.esiClient.request(op)
                return response.data
        except Exception as e:
            logging.error("Error retrieving Corporation-History {} from ESI".format(charid), e)
        return None


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    esi = EsiInterface()
    character = esi.getCharacter(94286636)  # Tablot Manzari
    corp = esi.getCorporationHistory(94286636)  # Bovril
    corp = esi.getCorporation(character['corporation_id'])  # Bovril
