class EsiConfig:
    import datetime
    SECRET_KEY = 'YouNeedToChangeThisToBeSecure!'
    PORT = 2020
    HOST = 'localhost'

    # -----------------------------------------------------
    # ESI Configs
    # -----------------------------------------------------
    ESI_DATASOURCE = 'tranquility'  # Change it to 'singularity' to use the test server
    ESI_SWAGGER_JSON = 'https://esi.tech.ccp.is/latest/swagger.json?datasource=%s' % ESI_DATASOURCE
    # Run the Application, then register on "https://developers.eveonline.com/applications"
    # You will then receive your Secret and Client keys
    ESI_SECRET_KEY = 'QUD3IsBSMa3AtEHHDMBhsTZsurL8s8FrauQoOF7f'  # your secret key
    ESI_CLIENT_ID = '50de89684c374189a25ccf83aa1d928a'  # your client ID
    ESI_CALLBACK = 'http://%s:%d/callback' % (HOST, PORT)  # the callback URI you gave CCP
    ESI_USER_AGENT = 'esi-python-test'


    # ------------------------------------------------------
    # Session settings for flask login
    # ------------------------------------------------------
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=30)
