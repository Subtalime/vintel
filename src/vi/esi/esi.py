from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
from vi.resources import resourcePath
from io import BytesIO
from esiconfig import EsiConfig
import threading
import logging
from esipy import EsiClient


class EsiServer:
    def __init__(self):
        httpd = HTTPServer((EsiConfig().HOST, EsiConfig().PORT), self.EsiHTTPRequestHandler)
        # httpd.socket = ssl.wrap_socket(httpd.socket, keyfile=resourcePath("vi/esi_rsa.pub"), certfile=resourcePath("vi/esi_rsa"), server_side=True)
        thread = threading.Thread(target=httpd.serve_forever)
        thread.setDaemon(True)
        try:
            thread.start()
        except Exception as e:
            logging.critical("HTTP-Server ", e)

    class EsiHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            logging.debug("Got a \"GET\" request")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Hello World")

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.end_headers()
            response = BytesIO()
            response.write(b'This is POST request. ')
            response.write(b'Received: ')
            response.write(body)
            logging.debug("Got a \"POST\" request : {}".format(body))
            self.wfile.write(response.getvalue())

def generate_token():
    import random
    import hmac
    import hashlib
    """Generates a non-guessable OAuth token"""
    chars = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    rand = random.SystemRandom()
    random_string = ''.join(rand.choice(chars) for _ in range(40))
    return hmac.new(
        EsiConfig().SECRET_KEY.encode('utf-8'),
        random_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
