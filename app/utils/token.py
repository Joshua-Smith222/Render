# app/utils/token.py
from __future__ import annotations

import os
from functools import wraps
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable, Any

from flask import request, jsonify, current_app
from jose import jwt, JWTError

ALGO = "HS256"


def _secret_key() -> str:
    return (
        (current_app.config.get("SECRET_KEY") if current_app else None)
        or os.getenv("SECRET_KEY")
        or "dev-secret"
    )


def encode_token(sub: str | int, role: Optional[str] = None, expires_in: int = 60 * 60 * 8) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(sub),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    if role:
        payload["role"] = role
    return jwt.encode(payload, _secret_key(), algorithm=ALGO)


# Optional alias if other code imports generate_token
def generate_token(sub: str | int, role: Optional[str] = None, expires_in: int = 60 * 60 * 8) -> str:
    return encode_token(sub, role, expires_in)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, _secret_key(), algorithms=[ALGO])


def _extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    h = auth_header.strip()
    lower = h.lower()
    while lower.startswith("bearer"):
        h = h[6:].strip()
        lower = h.lower()
    return h or None


def token_required(*roles: str) -> Callable[..., Any]:
    """
    Validates a Bearer token, enforces roles (if provided), and injects
    the subject into any of these parameter names your view might use:
      - current_user_id, user_id
      - current_customer_id, customer_id
      - current_mechanic_id, mechanic_id
      - current_user   <-- added for your routes
    Also injects 'current_role' if the view accepts it.
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = _extract_bearer_token(request.headers.get("Authorization", ""))
            if not token:
                return jsonify({"error": "Missing or invalid Authorization header"}), 401

            try:
                payload = decode_jwt(token)
            except JWTError:
                return jsonify({"error": "Invalid token"}), 401

            role = payload.get("role")
            if roles and role not in roles:
                return jsonify({"error": "Forbidden"}), 403

            sub = payload.get("sub")

            # Inject into whatever arg names the view actually declares
            code_vars = getattr(fn, "__code__", None)
            varnames = getattr(code_vars, "co_varnames", ()) if code_vars else ()

            for name in (
                "current_user_id",
                "user_id",
                "current_customer_id",
                "customer_id",
                "current_mechanic_id",
                "mechanic_id",
                "current_user",          # <-- new alias your tests need
            ):
                if name in varnames and name not in kwargs:
                    kwargs[name] = sub

            if "current_role" in varnames and "current_role" not in kwargs:
                kwargs["current_role"] = role

            return fn(*args, **kwargs)
        return wrapper
    return decorator
