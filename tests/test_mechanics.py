# tests/test_mechanics.py
from tests.base import BaseTestCase

class TestMechanics(BaseTestCase):
    def test_create_and_get(self):
        m = self.client.post("/mechanics/", json={"name": "Wrench", "specialty": "Brakes"})
        self.assertEqual(m.status_code, 201)
        mid = m.get_json()["id"]
        g = self.client.get(f"/mechanics/{mid}")
        self.assertEqual(g.status_code, 200)

    def test_update_not_found(self):
        r = self.client.put("/mechanics/999", json={"name": "Nope"})
        self.assertEqual(r.status_code, 404)
