import http.client
import json
import threading
import unittest
from app import create_server

KEY = 'test-key-for-local-tests-only'
ALERT = {'firstName': 'Alex', 'lastName': 'TestAlerte', 'dateOfBirth': '1980-01-15'}


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server('127.0.0.1', 0, KEY)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, payload, key=KEY, content_type='application/json', path='/v1/aml/screen'):
        conn = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        body = payload if isinstance(payload, str) else json.dumps(payload)
        conn.request('POST', path, body, {'X-API-Key': key, 'Content-Type': content_type})
        response = conn.getresponse()
        status, data = response.status, json.loads(response.read())
        conn.close()
        return status, data

    def test_match(self):
        self.assertEqual(self.request(ALERT), (200, {'isFlagged': True}))

    def test_no_match(self):
        self.assertEqual(self.request({**ALERT, 'lastName': 'TestClair'}), (200, {'isFlagged': False}))

    def test_different_birth_date(self):
        self.assertEqual(self.request({**ALERT, 'dateOfBirth': '1981-01-15'}), (200, {'isFlagged': False}))

    def test_normalization(self):
        self.assertEqual(self.request({'firstName': '  EMILE ', 'lastName': 'exemplefictif', 'dateOfBirth': '1975-12-03'}), (200, {'isFlagged': True}))

    def test_invalid_requests_never_return_false(self):
        for payload in ({}, [], None, 'bad json', {**ALERT, 'dateOfBirth': '1980-02-31'}, {**ALERT, 'dateOfBirth': '2999-01-01'}, {**ALERT, 'firstName': 42}, {**ALERT, 'unexpected': True}):
            with self.subTest(payload=payload):
                status, data = self.request(payload)
                self.assertEqual(status, 400)
                self.assertNotIn('isFlagged', data)

    def test_bad_key(self):
        self.assertEqual(self.request(ALERT, key='wrong')[0], 401)

    def test_content_type(self):
        self.assertEqual(self.request(ALERT, content_type='text/plain')[0], 415)

    def test_body_limit(self):
        self.assertEqual(self.request('x' * 65537)[0], 413)

    def test_unknown_route(self):
        self.assertEqual(self.request(ALERT, path='/missing')[0], 404)

    def test_health(self):
        conn = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        conn.request('GET', '/health')
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.read())['mode'], 'mock')
        conn.close()


if __name__ == '__main__':
    unittest.main()
