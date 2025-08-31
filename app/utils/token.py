# app/utils/token.py
import os
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT

# Prefer a dedicated JWT secret; fall back to Flask SECRET_KEY for convenience.
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "change-me"
ALGORITHM = os.getenv("JWT_ALG", "HS256")

def encode_token(sub, role=None, expires: timedelta | None = None) -> str:
    """Return a signed JWT string with standard claims.
    `sub` must be stringable; role is optional.
    """
    now = datetime.now(timezone.utc)
    exp = now + (expires or timedelta(hours=8))
    payload = {
        "sub": str(sub),                     # PyJWT 2.x expects sub as a string
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if role:
        payload["role"] = role
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode & verify a token, raising jwt exceptions on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
