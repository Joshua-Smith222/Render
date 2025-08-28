# tests/base.py
import unittest
from app import create_app
from app.extensions import db

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
            "CACHE_TYPE": "SimpleCache",
        })
        self.app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
            "CACHE_TYPE": "SimpleCache",
        })
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        # ✅ Seed a loginable customer using your model's fields
        from app.models import Customer
        c = Customer(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            address="123 Main St",
            phone="555-0000",
        )
        c.set_password("secret123")
        db.session.add(c)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def auth_header(self):
        resp = self.client.post("/login", json={"email": "test@example.com", "password": "secret123"})
        token = resp.get_json().get("token")
        return {"Authorization": f"Bearer {token}"}
