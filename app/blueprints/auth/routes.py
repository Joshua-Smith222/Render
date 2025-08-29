# app/blueprints/auth/routes.py
from flask import Blueprint, request, jsonify
from ...extensions import db  # not used directly here, but handy if you later log attempts
from ...models import Customer, Mechanic
from ...utils.token import generate_token  # expects signature like: generate_token(sub: str, role: str)

auth_bp = Blueprint("auth", __name__)


def _json():
    """Safely pull JSON, returning {} if body is empty or invalid JSON."""
    return request.get_json(silent=True) or {}


def _require(fields, data):
    """Validate required fields present and non-empty."""
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return f"Missing required field(s): {', '.join(missing)}"
    return None


@auth_bp.route("/login", methods=["POST"])
def customer_login():
    """
    Customer login.
    Body: { "email": "<email>", "password": "<plain text>" }
    Returns: { "token": "<jwt>" } on success, 401 otherwise.
    """
    data = _json()
    err = _require(["email", "password"], data)
    if err:
        return jsonify(error=err), 400

    email = data["email"].strip().lower()
    password = data["password"]

    cust = Customer.query.filter_by(email=email).first()
    if not cust or not hasattr(cust, "check_password") or not cust.check_password(password):
        return jsonify(error="Invalid credentials"), 401

    token = generate_token(sub=str(cust.customer_id), role="customer")
    return jsonify(token=token), 200


@auth_bp.route("/mechanics/login", methods=["POST"])
def mechanic_login():
    """
    Mechanic login.
    Body: { "email": "<email>", "password": "<plain text>" }
    Returns: { "token": "<jwt>" } on success, 401 otherwise.
    """
    data = _json()
    err = _require(["email", "password"], data)
    if err:
        return jsonify(error=err), 400

    email = data["email"].strip().lower()
    password = data["password"]

    mech = Mechanic.query.filter_by(email=email).first()
    if not mech or not hasattr(mech, "check_password") or not mech.check_password(password):
        return jsonify(error="Invalid credentials"), 401

    token = generate_token(sub=str(mech.mechanic_id), role="mechanic")
    return jsonify(token=token), 200
