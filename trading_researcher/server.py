"""Loopback-only JSON RPC. No model is given the operator credential."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from .codec import MAX_BYTES, Invalid, canonical, decode
from .coordination import Conflict, Denied


class RemoteError(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, url, token, timeout=10):
        parsed = urlsplit(url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port
                or parsed.username or parsed.password or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise Invalid('The client accepts only http://127.0.0.1:PORT')
        self.url, self.token, self.timeout = url.rstrip('/'), token, timeout

    def call(self, op, **args):
        request = Request(self.url + '/rpc',
                          data=canonical({'op': op, 'args': args}).encode('utf-8'),
                          headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        # Never expose bearer capabilities to an environment proxy or redirect target.
        opener = build_opener(ProxyHandler({}), NoRedirect())
        try:
            with opener.open(request, timeout=self.timeout) as response:
                return decode(response.read(MAX_BYTES + 1))
        except HTTPError as exc:
            try:
                body = decode(exc.read(MAX_BYTES + 1))
                message = body.get('error', 'RPC rejected')
            finally:
                exc.close()
            raise RemoteError(exc.code, message) from None


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_):
        # Avoid credential or model-content leakage through request logs.
        pass

    def _reply(self, code, body):
        raw = canonical(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        try:
            if self.path != '/rpc' or self.headers.get('Origin'):
                raise Denied('Only authenticated local RPC is available')
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                raise Denied('Invalid local host')
            if self.headers.get('Transfer-Encoding'):
                raise Invalid('Chunked requests are unavailable')
            length = int(self.headers.get('Content-Length', '-1'))
            if not 0 <= length <= MAX_BYTES:
                raise Invalid('Missing or oversized request body')
            if self.headers.get('Content-Type') != 'application/json':
                raise Invalid('Content-Type must be application/json')
            authorization = self.headers.get('Authorization', '')
            if not authorization.startswith('Bearer '):
                raise Denied('Invalid capability')
            request = decode(self.rfile.read(length))
            if (type(request) is not dict or set(request) != {'op', 'args'}
                    or type(request['op']) is not str or type(request['args']) is not dict):
                raise Invalid('Expected op and args object')
            result = self.server.broker.call(authorization[7:], request['op'], **request['args'])
            if request['op'] == 'status':
                result['scheduler_error'] = self.server.scheduler_error
            self._reply(200, result)
        except Denied as exc:
            self._reply(403, {'error': str(exc)})
        except Conflict as exc:
            self._reply(409, {'error': str(exc)})
        except (Invalid, ValueError, TypeError) as exc:
            self._reply(400, {'error': str(exc)})
        except Exception:
            self._reply(500, {'error': 'Controller failure; task state must be inspected'})


class LocalServer(ThreadingHTTPServer):
    # server_close must finish request handlers before the owning broker closes.
    daemon_threads = False

    def __init__(self, broker, port=0):
        self.broker = broker
        self.scheduler_error = None
        super().__init__(('127.0.0.1', port), Handler)
        self.url = f'http://127.0.0.1:{self.server_port}'

    def service_actions(self):
        try:
            self.broker.call(self.broker.admin_token, 'tick')
            self.scheduler_error = None
        except Exception as exc:
            error = type(exc).__name__
            if error != self.scheduler_error:
                print('Scheduler failed: ' + error + '; inspect operator status.', file=sys.stderr)
            self.scheduler_error = error
