# app/utils/token.py
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt  # PyJWT
from flask import request, jsonify, g

# Use a dedicated JWT secret if present; fall back to Flask SECRET_KEY.
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "change-me"
ALGORITHM = os.getenv("JWT_ALG", "HS256")

def encode_token(sub, role=None, expires: timedelta | None = None) -> str:
    """Create a signed JWT (sub must be stringable)."""
    now = datetime.now(timezone.utc)
    exp = now + (expires or timedelta(hours=8))
    payload = {
        "sub": str(sub),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if role:
        payload["role"] = role
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode/verify a JWT, raising jwt.* exceptions on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def token_required(role: str | None = None):
    """
    Decorator for protected endpoints.
    - Checks `Authorization: Bearer <token>` header
    - Verifies/decodes JWT
    - Optionally enforces a `role` claim
    - Stashes info on `flask.g`: g.jwt (dict), g.identity (sub)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401
            token = auth.split(" ", 1)[1].strip()
            try:
                payload = decode_token(token)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Invalid or expired token"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid or expired token"}), 401

            if role and payload.get("role") != role:
                return jsonify({"error": "Forbidden"}), 403

            g.jwt = payload
            g.identity = payload.get("sub")  # string per JWT spec
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def get_jwt() -> dict | None:
    return getattr(g, "jwt", None)

def get_jwt_identity() -> str | None:
    return getattr(g, "identity", None)
