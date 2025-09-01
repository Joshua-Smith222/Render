# app/blueprints/auth/routes.py
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
from app.extensions import db
from app.models import Customer
from app.utils.token import encode_token

auth_bp = Blueprint("auth", __name__)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

login_schema = LoginSchema()

@auth_bp.post("/login")
def login():
    """Simple customer login that returns a JWT."""
    data = request.get_json(silent=True) or {}
    try:
        data = login_schema.load(data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    user = Customer.query.filter_by(email=data["email"]).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # Support either a check_password method or a stored password_hash
    if hasattr(user, "check_password") and callable(user.check_password):
        valid = user.check_password(data["password"])
    else:
        from werkzeug.security import check_password_hash
        valid = check_password_hash(getattr(user, "password_hash", ""), data["password"])

    if not valid:
        return jsonify({"error": "Invalid credentials"}), 401

    uid = getattr(user, "customer_id", None) or getattr(user, "id", None) or user.email
    token = encode_token(uid, role="customer")
    return jsonify({"token": token}), 200
