# tests/test_inventory.py
from tests.base import BaseTestCase

class TestInventory(BaseTestCase):
    def test_create_list_get(self):
        c = self.client.post("/inventory/", json={"sku": "ABC123", "name": "Oil Filter", "qty": 10})
        self.assertEqual(c.status_code, 201)
        i = c.get_json()["id"]
        l = self.client.get("/inventory/")
        self.assertEqual(l.status_code, 200)
        g = self.client.get(f"/inventory/{i}")
        self.assertEqual(g.status_code, 200)

    def test_update_qty(self):
        c = self.client.post("/inventory/", json={"sku": "XYZ", "name": "Brake Pads"}).get_json()
        r = self.client.put(f"/inventory/{c['id']}", json={"qty": 5})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["qty"], 5)

    def test_delete_not_found(self):
        r = self.client.delete("/inventory/9999")
        self.assertEqual(r.status_code, 404)
