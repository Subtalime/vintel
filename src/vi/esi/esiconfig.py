class EsiConfig:
    import vi.version

    # this will be set during authentication
    def setSecretKey(self, value: str):
        self.ESI_SECRET_KEY = value
    def getSecretKey(self):
        return self.ESI_SECRET_KEY

    # Local Call-Back Port
    PORT = 2020
    # where the Webserver will be running
    HOST = 'localhost'
    URI = 'callback'

    # -----------------------------------------------------
    # ESI Configs
    # -----------------------------------------------------
    ESI_DATASOURCE = 'tranquility'  # Change it to 'singularity' to use the test server
    ESI_SWAGGER_JSON = 'https://esi.tech.ccp.is/latest/swagger.json?datasource=%s' % ESI_DATASOURCE
    # Run the Application, then register on "https://developers.eveonline.com/applications"
    # You will then receive your Secret and Client keys
    ESI_SECRET_KEY = ''  # your secret key will be filled in by SSo-Authentication
    ESI_CLIENT_ID = ''  # your client ID
    # ESI_CLIENT_ID = '50de89684c374189a25ccf83aa1d928a'  # your client ID
    ESI_CALLBACK = 'http://%s:%d/%s' % (HOST, PORT, URI)  # the callback URI you gave CCP
    ESI_USER_AGENT = vi.version.PROGNAME
