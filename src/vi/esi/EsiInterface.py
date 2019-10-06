import logging
from esipy.utils import generate_code_verifier
from esipy import EsiClient, EsiApp, EsiSecurity
from esipy.security import APIException
from esiconfig import EsiConfig
import json
from urllib.parse import urlparse, parse_qs
import vi.version
import webbrowser
import threading
from vi.cache.cache import Cache
from http.server import HTTPServer, BaseHTTPRequestHandler

secretKey = None

class EsiInterface:
    instance = None
    # make it a Singleton
    class __OnceOnly:
        def __init__(self):
            global secretKey
            logging.debug("Creating ESI access")
            self.authenticated = False
            self.esiConfig = EsiConfig()
            self.server = None
            self.headers = {'User-Agent': "{} Intel Management Tool".format(vi.version.PROGNAME)}
            self.codeverifier = generate_code_verifier()
            try:
                # this uses PKCE (pixie) authorisation with ESI
                self.security = EsiSecurity(
                    # The application (matching ESI_CLIENT_ID) must have the same Callback configured!
                    redirect_uri=self.esiConfig.ESI_CALLBACK,
                    client_id=self.esiConfig.ESI_CLIENT_ID,
                    code_verifier=self.codeverifier,
                    headers=self.headers
                )

                # this authentication can be used with all ESI calls
                self.esiClient = EsiClient(security=self.security,
                                           retry_requests=True,
                                           headers=self.headers
                                           )
                self.apiInfo = None
                tokenKey = json.loads(Cache().getFromCache("esi_token"))
                while not self.apiInfo:
                    try:
                        if secretKey:
                            self.esiConfig.setSecretKey(secretKey)
                            secretKey = None
                            self.tokens = self.security.auth(self.esiConfig.getSecretKey())
                            self.apiInfo = self.security.verify()
                            # store the Token
                            Cache().putIntoCache("esi_token", json.dumps(self.tokens))
                        elif tokenKey:
                            self.security.update_token(tokenKey)
                            self.apiInfo = self.security.refresh()
                        else:
                            self.waitForSecretKey()
                    except APIException as e:
                        logging.error("EsiAPI Error", e)
                        self.waitForSecretKey()
                    except AttributeError as e:
                        logging.error("EsiAttribute Error", e)
                        self.waitForSecretKey()
                    except Exception as e:
                        logging.error("Some unexpected error in Esi", e)

                logging.debug("ESI loading Swagger...")
                # outputs a load of data in Debug
                oldSetting = logging.getLogger().getEffectiveLevel()
                logging.getLogger().setLevel(logging.ERROR)
                self.esiApp = EsiApp().get_latest_swagger
                # Reset logging to old level
                logging.getLogger().setLevel(oldSetting)
                logging.debug("ESI loading Swagger...complete")
                self.authenticated = True
                logging.debug("Finished authorizing with ESI")
            except Exception as e:
                logging.critical("Error authenticating with ESI", e)
                exit(-1)

        def waitForSecretKey(self):
            global secretKey
            redirected = False
            while not secretKey:
                if not self.server:
                    self.server = self.EsiWebServer(self.esiConfig)
                    self.server.start()
                if not redirected:
                    ssoUri = self.security.get_auth_uri(
                        state="Authentication for {}".format(vi.version.PROGNAME),
                        scopes=None
                    )
                    webbrowser.open(ssoUri)
                    redirected = True
            if self.server:
                self.server.stop()
                self.server = None

        class EsiWebServer(object):
            def __init__(self, esiConfigInstance: EsiConfig):
                self.esiConfig = esiConfigInstance
                self.httpd = HTTPServer((self.esiConfig.HOST, self.esiConfig.PORT), self.EsiHTTPRequestHandler)
                self.server_thread = threading.Thread(target=self.httpd.serve_forever)
                self.server_thread.daemon = True

            def start(self):
                self.server_thread.start()

            def stop(self):
                self.httpd.shutdown()
                self.httpd.server_close()

            class EsiHTTPRequestHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    logging.debug("Got a \"GET\" request: {}".format(self.requestline))
                    self.send_response(200)
                    self.end_headers()
                    try:
                        urlobjects = urlparse(self.requestline)
                        thisquery = parse_qs(urlobjects.query)
                        if thisquery['code']:
                            global secretKey
                            secretKey = thisquery['code'][0]
                            self.wfile.write(b"You can now close this window")
                    except Exception as e:
                        logging.error("Unexpected response: {}".format(self.requestline))
                        self.wfile.write(b"I don't know what you are on about")

        def __str__(self):
            return repr(self)

    def __init__(self):
        if not EsiInterface.instance:
            EsiInterface.instance = EsiInterface.__OnceOnly()
    def __getattr__(self, name):
        return getattr(self.instance, name)

    def getCharacter(self, charid: int):
        response = None
        try:
            self.security.verify()
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
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_corporations_corporation_id'] (corporation_id=corpid)
                response = self.esiClient.request(op)
                return response.data
        except Exception as e:
            logging.error("Error retrieving Corporation {} from ESI".format(corpid), e)
        return None

    def getCorporationHistory(self, charid: int):
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_characters_character_id_corporationhistory'] (character_id=charid)
                response = self.esiClient.request(op)
                return response.data
        except Exception as e:
            logging.error("Error retrieving Corporation-History {} from ESI".format(charid), e)
        return None

    def getCharacterId(self, charname: str, strict: bool=True):
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_search'] (categories='character', search=charname, strict=strict)
                response = self.esiClient.request(op)
                return response.data
        except Exception as e:
            logging.error("Error retrieving Corporation-History {} from ESI".format(charid), e)
        return response

    def getCharacterAvatar(self, charid: int):
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_characters_character_id_portrait'] (character_id=charid)
                response = self.esiClient.request(op)
                return response.data
        except Exception as e:
            logging.error("Error retrieving Corporation-History {} from ESI".format(charid), e)
        return response



if __name__ == "__main__":
    import requests
    logging.getLogger().setLevel(logging.DEBUG)
    esi = EsiInterface()
    charid = esi.getCharacterId("Tablot Manzari")
    esi2 = EsiInterface()
    charid = charid['character'][0]
    character = esi.getCharacter(charid)  # Tablot Manzari
    print(character)
    avatars = esi.getCharacterAvatar(charid)  # Tablot Manzari
    imageurl = avatars["px64x64"]
    avatar = requests.get(imageurl).content
    corphist = esi.getCorporationHistory(charid)  # Bovril
    print(corphist)
    corp = esi.getCorporation(character['corporation_id'])  # Bovril
    print(corp)
