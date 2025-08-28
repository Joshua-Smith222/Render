from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields
from app.models import Customer
from app.utils.token import encode_token

auth_bp = Blueprint("auth", __name__)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

login_schema = LoginSchema()

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    errors = login_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 400

    user = Customer.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    uid = getattr(user, "customer_id", None) or getattr(user, "id")
    return jsonify({"token": encode_token(uid)}), 200
