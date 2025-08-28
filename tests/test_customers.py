# tests/test_customers.py
from tests.base import BaseTestCase

class TestCustomers(BaseTestCase):
    def test_create_customer(self):
        payload = {"first_name": "Alice", "last_name": "Smith", "address": "42 Oak Ave", "phone": "555-1234", "email": "alice@example.com", "password": "pw12345"}
        r = self.client.post("/customers/", json=payload)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["email"], payload["email"])

    def test_list_customers(self):
        r = self.client.get("/customers/")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.get_json(), list)

    def test_get_customer_not_found(self):
        r = self.client.get("/customers/9999")
        self.assertEqual(r.status_code, 404)

    def test_update_customer_validation_error(self):
        # Create first
        c = self.client.post("/customers/", json={"name": "Bob", "email": "bob@x.com", "password": "pw"}).get_json()
        # Bad update
        r = self.client.put(f"/customers/{c['id']}", json={"email": "not-an-email"})
        self.assertIn(r.status_code, (400, 422))

    def test_delete_customer(self):
        c = self.client.post("/customers/", json={"name": "Del", "email": "del@x.com", "password": "pw"}).get_json()
        r = self.client.delete(f"/customers/{c['id']}")
        self.assertEqual(r.status_code, 204)
