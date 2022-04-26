
import os
from random import randint
import subprocess
import re
import sys
from typing import Any

import tornado
import tornado.web
import tornado.gen
from tornado.httputil import HTTPHeaders, parse_response_start_line
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

_fetch = AsyncHTTPClient().fetch
import tornado.websocket
class DevelopmentStaticFileHandler(tornado.web.RequestHandler):

    _headers_skip = ["Transfer-Encoding"]

    @staticmethod
    def _setup(port: int = 0):
        if hasattr(DevelopmentStaticFileHandler, "_process"):
            return

        import manus_webshell

        if port == 0:
            port = 8081 # 10000 + randint(0, 1000)

        cwd = os.path.dirname(os.path.dirname(manus_webshell.__file__))

        command = ["npm", "run", "servedev"]

        envvars = dict(**os.environ)

        envvars["PORT"] = str(port)
        envvars["BROWSER"] = "none"
        envvars["HOST"] = "localhost"
        envvars["PUBLIC_URL"] = "./"

        DevelopmentStaticFileHandler._rewrite = re.compile(b"=\"/static/")
        DevelopmentStaticFileHandler._backend = 'localhost:{}'.format(port)
        DevelopmentStaticFileHandler._process = subprocess.Popen(command, stdout=sys.stdout, stderr=subprocess.STDOUT, env=envvars, cwd=cwd)
        
        try:
            DevelopmentStaticFileHandler._process.wait(4) 
            raise RuntimeError("Unable to start webpack dev server")
        except subprocess.TimeoutExpired:
            pass

    def __init__(self, application: "Application", request: "httputil.HTTPServerRequest", **kwargs: Any) -> None:
        super().__init__(application, request, **kwargs)
        #DevelopmentStaticFileHandler._setup(kwargs.get("port", 10000 + randint(0, 1000)))

    async def get(self, path):
        
        url = 'http://{}/{}'.format(self._backend, path)

        client = AsyncHTTPClient()

        if path == "ws":
            #self.request.headers["Host"] = self._backend
            #self.request.headers["Origin"] = 'http://{}/'.format(self._backend)
            request = HTTPRequest(url,
                 headers = self.request.headers,
                 header_callback = self._handle_headers,
                 streaming_callback = self._handle_chunk,
                 decompress_response = False)

            print(url)

            

            response = await _fetch(request)

            self.finish()
        else:

            response = await client.fetch(url, raise_error=False)

            for k, v in response.headers.get_all():
                if k in DevelopmentStaticFileHandler._headers_skip:
                    continue 
                self.set_header(k, v)

            self.set_status(response.code)
            
            if response.headers["Content-Type"].startswith("text/html"):
                content = re.sub(self._rewrite, b"=\"./static/", response.body)
            else:
                content = response.body

            self.write(content)
            self.finish()

    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')

    def _handle_headers(self, headers):
        if hasattr(self, "_theaders"):
            if headers == "\r\n":
                for kv in self._theaders.get_all():
                    self.add_header(kv[0], kv[1])
                del self._theaders
                return
            try:
                self._theaders.parse_line(headers)
            except:
                return
        else:
            r = parse_response_start_line(headers)
            self.set_status(r.code, r.reason)
            self._theaders = HTTPHeaders()

    def _handle_chunk(self, chunk):
        print("chunk")
        self.write(chunk)
        self.flush()