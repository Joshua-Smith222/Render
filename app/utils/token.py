# app/utils/jwt_utils.py
from datetime import datetime, timedelta, UTC
from functools import wraps

from flask import current_app, request, jsonify
from jose import jwt, JWTError


ALGORITHM = "HS256"
EXPIRE_MINUTES = 60


def _jwt_secret():
    """
    Single source of truth for the signing key.
    We prefer JWT_SECRET, else SECRET_KEY.
    create_app() already sets JWT_SECRET = SECRET_KEY by default.
    """
    return current_app.config.get("JWT_SECRET") or current_app.config["SECRET_KEY"]


def encode_token(customer_id: int | str) -> str:
    payload = {
        "sub": str(customer_id),
        "exp": datetime.now(UTC) + timedelta(minutes=EXPIRE_MINUTES),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def token_required(f):
    """
    Decorator to require a valid token for accessing a route.
    Injects `customer_id` as the first arg to the view if valid.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization") or ""
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Authorization header missing or invalid"}), 401

        customer_id = decode_token(parts[1])
        if not customer_id:
            return jsonify({"error": "Invalid token"}), 401

        return f(customer_id, *args, **kwargs)

    return decorated
