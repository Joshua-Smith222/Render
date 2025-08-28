from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC
from flask import current_app # Replace with a strong key, or use `app.config`
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60  # Token expires in 1 hour
SECRET_KEY = "Takobre022293!"  # This should be set in your app config for security
def encode_token(customer_id):
    payload = {
        "sub": str(customer_id),
        "exp": datetime.now(UTC) + timedelta(minutes=EXPIRE_MINUTES)
    }
    print(f"Encoding token with key:{SECRET_KEY}, payload: {payload}")
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token):
    print(f"Decoding token: {token}")
    try:
        print(f"Decoding with key: {SECRET_KEY}")
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")
        return payload["sub"]
    except JWTError as e:
        print(f"JWT decode error: {type(e)} - {e}")
        return None
def token_required(f):
    """
    Decorator to require a valid token for accessing a route.
    """
    from functools import wraps
    from flask import request, jsonify, current_app

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        print(f"Authorization header: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid"}), 401

        parts = auth_header.split()
        if len(parts) != 2:
            return jsonify({"error": "Invalid authorization header format"}), 401

        token = parts[1]
        print(f"Extracted token: {token}")
        customer_id = decode_token(token)
        print(f"Failed to decode token")
        if not customer_id:
            return jsonify({"error": "Invalid token"}), 401
        print(f"Token valid for customer_id: {customer_id}")
        return f(customer_id, *args, **kwargs)

    return decorated_function
