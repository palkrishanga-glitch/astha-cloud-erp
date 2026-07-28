import jwt
import hashlib
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

JWT_SECRET = os.getenv("JWT_SECRET", "ASTHA_ERP_SECRET_KEY_2026_MASTER_ENTERPRISE_KEY")
JWT_ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hashes password using SHA256 with salt."""
    salt = "ASTHA_BUILDERS_SALT_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def generate_jwt_token(user_id: int, name: str, email: str, role: str) -> str:
    """Generates JWT token valid for 24 hours."""
    payload = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    """Decodes and validates JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(roles=None):
    """
    Decorator for verifying JWT token and Role-Based Access Control (RBAC).
    Roles can be a list: ['Admin', 'Manager', 'Accountant', 'Staff']
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            
            if not token:
                return jsonify({"status": "ERROR", "message": "Authentication token missing"}), 401
            
            payload = decode_jwt_token(token)
            if not payload:
                return jsonify({"status": "ERROR", "message": "Invalid or expired token"}), 401
            
            user_role = payload.get("role")
            if roles and user_role not in roles:
                return jsonify({"status": "ERROR", "message": f"Permission denied for role: {user_role}"}), 403
            
            request.current_user = payload
            return f(*args, **kwargs)
        return decorated
    return decorator
