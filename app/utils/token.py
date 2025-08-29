# app/utils/token.py
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import current_app, request, jsonify, g
import inspect
import jwt

def _jwt_secret():
    return current_app.config.get("JWT_SECRET", current_app.config["SECRET_KEY"])

def _jwt_algo():
    return current_app.config.get("JWT_ALGO", "HS256")

def generate_token(sub: str, role: str = "customer", expires_in: int = 24 * 3600) -> str:
    payload = {
        "sub": str(sub),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algo())

def decode_token(token: str) -> dict:
    return jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algo()])

def token_required(role: str | None = None):
    """
    @token_required()                # validates any role
    @token_required("mechanic")      # restricts to mechanics
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            parts = auth.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify(error="Missing or invalid Authorization header"), 401

            try:
                payload = decode_token(parts[1])
            except jwt.ExpiredSignatureError:
                return jsonify(error="Token expired"), 401
            except jwt.InvalidTokenError:
                return jsonify(error="Invalid token"), 401

            if role and payload.get("role") != role:
                return jsonify(error="Forbidden"), 403

            # Stash on g for any route to read
            sub = payload.get("sub")
            if sub is None:
                return jsonify(error="Invalid token: missing sub"), 401

            g.jwt = payload
            g.current_user_id = int(sub)
            if payload.get("role") == "mechanic":
                g.current_mechanic_id = int(sub)
            else:
                g.current_customer_id = int(sub)

            # Only inject kwargs the view actually declares
            params = set(inspect.signature(fn).parameters.keys())
            # Always support a generic 'current_user' param (id as int)
            if "current_user" in params:
                kwargs.setdefault("current_user", int(sub))
            if payload.get("role") == "mechanic":
                if "current_mechanic_id" in params:
                    kwargs.setdefault("current_mechanic_id", int(sub))
            else:
                if "current_customer_id" in params:
                    kwargs.setdefault("current_customer_id", int(sub))

            return fn(*args, **kwargs)
        return wrapper
    return decorator
