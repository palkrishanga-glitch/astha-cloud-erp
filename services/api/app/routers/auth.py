from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from ..database import get_db
from ..models import User, Role, UserSession, LoginHistory, AuditLog
from ..auth import (
    hash_password, hash_owner_pin, validate_password_policy, create_access_token,
    verify_token_header, verify_owner_pin, MAX_FAILED_ATTEMPTS, LOCK_DURATION_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])

class FirstTimeSetupSchema(BaseModel):
    owner_username: str = "owner"
    owner_full_name: str = "Astha Owner"
    owner_email: str
    owner_mobile: str
    owner_password: str
    owner_pin: str = "1234"

class LoginSchema(BaseModel):
    identifier: str # Username, Email, or Mobile
    password: str

class OwnerPinVerifySchema(BaseModel):
    owner_id: str
    owner_pin: str

class UserProfileUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    theme_preference: Optional[str] = "dark"
    new_password: Optional[str] = None

@router.post("/setup", status_code=status.HTTP_201_CREATED)
def first_time_setup(payload: FirstTimeSetupSchema, db: Session = Depends(get_db)):
    """
    First Time Setup:
    Automatically creates Owner account, default Roles (Owner, Admin, Manager, Accountant, Cashier, Sales, Store, Viewer),
    and initializes system security.
    """
    existing_owner = db.query(User).first()
    if existing_owner:
        raise HTTPException(status_code=400, detail="First-time setup has already been completed.")

    valid, msg = validate_password_policy(payload.owner_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    # 1. Initialize Built-in Roles
    built_in_roles = [
        ("Owner", "Unrestricted master system control"),
        ("Administrator", "System administration and settings control"),
        ("Manager", "Operational management and approvals"),
        ("Accountant", "Double-entry accounting, ledgers, and tax returns"),
        ("Cashier", "POS sales billing and cash register management"),
        ("Sales Executive", "Sales quotations, orders, and customer management"),
        ("Purchase Executive", "Supplier purchase orders and invoices"),
        ("Store Manager", "Inventory stock management and warehouse transfers"),
        ("Warehouse Staff", "Physical stock entries"),
        ("Delivery Staff", "Challan and delivery tracking"),
        ("Viewer", "Read-only access across all views")
    ]

    role_map = {}
    for r_name, r_desc in built_in_roles:
        r = Role(name=r_name, description=r_desc)
        db.add(r)
        db.flush()
        role_map[r_name] = r.id

    # 2. Create Owner Account
    owner_user = User(
        employee_id="EMP-001",
        username=payload.owner_username.strip(),
        full_name=payload.owner_full_name.strip(),
        email=payload.owner_email.strip(),
        mobile=payload.owner_mobile.strip(),
        password_hash=hash_password(payload.owner_password),
        owner_pin_hash=hash_owner_pin(payload.owner_pin),
        role_id=role_map["Owner"],
        department="Executive",
        designation="Owner & MD",
        status="ACTIVE"
    )
    db.add(owner_user)
    db.commit()
    db.refresh(owner_user)

    return {
        "status": "SUCCESS",
        "message": "First-time setup completed successfully.",
        "owner_username": owner_user.username,
        "owner_id": owner_user.id
    }

@router.post("/login")
def login_user(payload: LoginSchema, db: Session = Depends(get_db)):
    """
    Login User via Username, Email, OR Mobile Number.
    Checks password policy, enforces account lock on failed attempts, and records Login History.
    """
    identifier = payload.identifier.strip()
    
    # Query user by username, email, or mobile
    user = db.query(User).filter(
        (User.username == identifier) |
        (User.email == identifier) |
        (User.mobile == identifier)
    ).first()

    if not user:
        # Record failed attempt
        hist = LoginHistory(username=identifier, status="FAILED", failure_reason="User not found")
        db.add(hist)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid login credentials.")

    # Check lock status
    if user.status == "BLOCKED" or user.status == "SUSPENDED":
        raise HTTPException(status_code=403, detail=f"Account is currently {user.status}. Contact Administrator.")

    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=403, detail="Account is temporarily locked due to consecutive failed attempts.")

    # Verify Password
    if user.password_hash != hash_password(payload.password):
        user.failed_login_attempts += 1
        failure_msg = f"Invalid password (Attempt {user.failed_login_attempts}/{MAX_FAILED_ATTEMPTS})"
        
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
            failure_msg = f"Account locked for {LOCK_DURATION_MINUTES} minutes due to multiple failed attempts."
            
            # Audit log entry
            audit = AuditLog(
                user_id=user.id,
                role_name=user.role.name if user.role else "User",
                module="Authentication",
                action="ACCOUNT_LOCKED",
                status="SECURITY_ALERT"
            )
            db.add(audit)

        hist = LoginHistory(user_id=user.id, username=user.username, status="FAILED", failure_reason=failure_msg)
        db.add(hist)
        db.commit()
        raise HTTPException(status_code=401, detail=failure_msg)

    # Reset failed attempts upon successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()

    # Record login session
    session_token = create_access_token(user.id, user.username, user.role.name if user.role else "User")
    sess = UserSession(user_id=user.id, session_token=session_token)
    hist = LoginHistory(user_id=user.id, username=user.username, status="SUCCESS")
    
    db.add(sess)
    db.add(hist)
    db.commit()

    return {
        "status": "SUCCESS",
        "token": session_token,
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.name if user.role else "User",
        "theme_preference": user.theme_preference
    }

@router.post("/verify-owner-pin")
def verify_owner_pin_endpoint(payload: OwnerPinVerifySchema, db: Session = Depends(get_db)):
    """Verifies Owner PIN for sensitive operations."""
    if verify_owner_pin(db, payload.owner_id, payload.owner_pin):
        return {"status": "VERIFIED", "valid": True}
    raise HTTPException(status_code=403, detail="Invalid Owner PIN.")

@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: dict = Depends(verify_token_header)):
    """Lists all user accounts."""
    users = db.query(User).all()
    return [{
        "id": u.id,
        "employee_id": u.employee_id,
        "username": u.username,
        "full_name": u.full_name,
        "email": u.email,
        "mobile": u.mobile,
        "role": u.role.name if u.role else "User",
        "status": u.status,
        "last_login": str(u.last_login) if u.last_login else None
    } for u in users]
