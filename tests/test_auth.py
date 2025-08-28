# tests/test_auth.py
from tests.base import BaseTestCase

class TestAuth(BaseTestCase):
    def test_login_success(self):
        r = self.client.post("/login", json={"email": "test@example.com", "password": "secret123"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("token", r.get_json())

    def test_login_wrong_password(self):
        r = self.client.post("/login", json={"email": "test@example.com", "password": "nope"})
        self.assertEqual(r.status_code, 401)

    def test_login_bad_payload(self):
        r = self.client.post("/login", json={"email": "not-an-email"})
        self.assertIn(r.status_code, (400, 422))
