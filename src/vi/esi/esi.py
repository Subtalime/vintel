import logging
from esipy.utils import generate_code_verifier
from esipy import EsiClient, EsiApp, EsiSecurity
from esiconfig import EsiConfig
import vi.version

class EsiInterface:
    def __init__(self):
        logging.debug("Creating ESI access")
        # this uses PKCE (pixie) authorisation with ESI
        self.security = EsiSecurity(
            # The application (matching ESI_CLIENT_ID) must have the same Callback configured!
            redirect_uri=EsiConfig().ESI_CALLBACK,
            client_id=EsiConfig().ESI_CLIENT_ID,
            code_verifier=generate_code_verifier(),
            headers={'User-Agent': vi.version.PROGNAME}
        )

        # this authentication can be used with all ESI calls
        self.esiClient = EsiClient(security=self.security)


        self.esiApp = EsiApp().get_latest_swagger
        logging.debug("Finished authorizing with ESI (using PKCE)")

        # op = esiApp.op(character_id=33333)
