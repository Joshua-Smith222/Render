# tests/test_service_tickets.py
from tests.base import BaseTestCase

class TestServiceTickets(BaseTestCase):
    def test_list_requires_auth(self):
        r = self.client.get("/service_tickets/")
        self.assertIn(r.status_code, (401, 422))  # depends on your decorator

    def test_create_and_get_with_auth(self):
        # You might need to seed a vehicle & customer in setUp if required by FK
        headers = self.auth_header()
        c_ticket = self.client.post(
            "/service_tickets/",
            json={"vehicle_id": 1, "customer_id": 1, "notes": "Check brakes"},
            headers=headers,
        )
        self.assertEqual(c_ticket.status_code, 201)
        tid = c_ticket.get_json()["id"]
        g = self.client.get(f"/service_tickets/{tid}", headers=headers)
        self.assertEqual(g.status_code, 200)

    def test_update_unauthorized(self):
        r = self.client.put("/service_tickets/1", json={"status": "closed"})
        self.assertIn(r.status_code, (401, 422))

    def test_assign_mechanics_parts(self):
        headers = self.auth_header()
        # Create ticket first
        t = self.client.post("/service_tickets/", json={"vehicle_id": 1, "customer_id": 1}, headers=headers).get_json()
        # Assign
        a = self.client.post(f"/service_tickets/{t['id']}/assign", json={"mechanic_ids": [], "inventory_ids": []}, headers=headers)
        self.assertEqual(a.status_code, 200)
