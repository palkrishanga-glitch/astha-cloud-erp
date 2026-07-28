import os
import re
import uuid
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, AuditLog, LoginHistory

SECRET_KEY = os.getenv("ASTHA_JWT_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15

def validate_password_policy(password: str) -> Tuple[bool, str]:
    """
    Enforces Part 3 Password Policy:
    Min length 8 chars (12 recommended), Uppercase, Lowercase, Number, Special Char.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\+\=]", password):
        return False, "Password must contain at least one special character."
    return True, "Valid"

def hash_password(password: str) -> str:
    """Non-reversible secure SHA-256 hash with salt."""
    salt = "ASTHA_ERP_SALT_2026"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def hash_owner_pin(pin: str) -> str:
    """Hashes sensitive action Owner PIN."""
    return hashlib.sha256(("ASTHA_PIN_" + pin).encode("utf-8")).hexdigest()

def create_access_token(user_id: str, username: str, role_name: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {
        "sub": user_id,
        "username": username,
        "role": role_name,
        "jti": str(uuid.uuid4()) # Unique token ID prevents duplicate tokens
    }
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

def verify_token_header(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Anonymous access is strictly denied."
        )
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token."
        )
    return payload

def verify_owner_pin(db: Session, owner_user_id: str, pin_input: str) -> bool:
    """Verifies Owner PIN for sensitive operations (Database restore, delete invoice, edit opening balance)."""
    user = db.query(User).filter(User.id == owner_user_id).first()
    if not user or not user.owner_pin_hash:
        return False
    return user.owner_pin_hash == hash_owner_pin(pin_input)
