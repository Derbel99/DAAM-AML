"""API AML fictive, sans dependances externes. Python 3.10+."""
import hmac
import json
import os
import re
import unicodedata
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WATCHLIST = json.loads((ROOT / 'mock_watchlist.json').read_text(encoding='utf-8'))
MAX_BODY = 65536


def normalize(value):
    text = unicodedata.normalize('NFKD', value)
    return ' '.join(''.join(c for c in text if not unicodedata.combining(c)).casefold().split())


def screen(payload):
    if not isinstance(payload, dict):
        raise ValueError('Le corps doit etre un objet JSON.')
    if set(payload) - {'firstName', 'lastName', 'dateOfBirth'}:
        raise ValueError('Champ inconnu. Champs acceptes: firstName, lastName, dateOfBirth.')
    for field in ('firstName', 'lastName', 'dateOfBirth'):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 100:
            raise ValueError(f'{field} est requis et doit etre une chaine de 1 a 100 caracteres.')
    dob = payload['dateOfBirth']
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', dob):
        raise ValueError('dateOfBirth doit etre au format YYYY-MM-DD.')
    try:
        birthday = date.fromisoformat(dob)
    except ValueError:
        raise ValueError('dateOfBirth est une date invalide.') from None
    if birthday > date.today():
        raise ValueError('dateOfBirth ne peut pas etre dans le futur.')
    flagged = any(
        normalize(payload['firstName']) == normalize(entry['firstName'])
        and normalize(payload['lastName']) == normalize(entry['lastName'])
        and dob == entry['dateOfBirth']
        for entry in WATCHLIST
    )
    return {'isFlagged': flagged}


class Handler(BaseHTTPRequestHandler):
    server_version = 'AMLMock/1.0'

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        # Pas de donnees client, de corps ou de cle API dans les logs.
        pass

    def reply(self, status, body):
        encoded = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == '/health':
            self.reply(200, {'status': 'ok', 'mode': 'mock'})
        else:
            self.reply(404, {'error': 'not_found'})

    def do_POST(self):
        if self.path != '/v1/aml/screen':
            self.reply(404, {'error': 'not_found'})
            return
        supplied = self.headers.get('X-API-Key', '')
        if not hmac.compare_digest(supplied.encode(), self.server.api_key.encode()):
            self.reply(401, {'error': 'unauthorized'})
            return
        if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            self.reply(415, {'error': 'application_json_required'})
            return
        if self.headers.get('Transfer-Encoding'):
            self.reply(400, {'error': 'transfer_encoding_not_supported'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.reply(400, {'error': 'invalid_content_length'})
            return
        if size <= 0 or size > MAX_BODY:
            self.reply(413 if size > MAX_BODY else 400, {'error': 'invalid_body_size'})
            return
        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError('Corps incomplet.')
            result = screen(json.loads(raw))
        except (ValueError, UnicodeDecodeError):
            self.reply(400, {'error': 'invalid_request', 'message': 'Verifier firstName, lastName et dateOfBirth (YYYY-MM-DD).'})
            return
        except TimeoutError:
            self.reply(408, {'error': 'request_timeout'})
            return
        self.reply(200, result)


def create_server(host, port, api_key):
    if not api_key or len(api_key) < 16:
        raise ValueError('AML_API_KEY doit contenir au moins 16 caracteres.')
    server = ThreadingHTTPServer((host, port), Handler)
    server.api_key = api_key
    return server


if __name__ == '__main__':
    server = create_server(os.getenv('HOST', '127.0.0.1'), int(os.getenv('PORT', '8000')), os.getenv('AML_API_KEY', ''))
    print(f'API AML MOCK sur http://{server.server_address[0]}:{server.server_address[1]}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
