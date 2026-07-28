import os
import shutil
import zipfile
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from ..database import get_db
from ..models import AuditLog, User
from ..auth import verify_owner_pin

router = APIRouter(prefix="/backup", tags=["Backup & Restore System"])

BACKUP_DIR = os.path.abspath("./backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

class RestoreBackupSchema(BaseModel):
    backup_file_name: str
    owner_pin: str = Field(..., description="Owner PIN mandatory for database restore")
    performed_by: str = "OWNER"

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_database_backup(db: Session = Depends(get_db)):
    """
    Part 12 Backup System:
    Creates a compressed timestamped zip archive of the SQLite database and settings.
    """
    db_file = "./astha_erp.db"
    if not os.path.exists(db_file):
        db_file = "./test_astha.db"

    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"ASTHA_ERP_Backup_{timestamp_str}.zip"
    zip_filepath = os.path.join(BACKUP_DIR, zip_filename)

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(db_file):
            zipf.write(db_file, arcname="astha_erp.db")
        if os.path.exists("./config/config.json"):
            zipf.write("./config/config.json", arcname="config.json")

    audit = AuditLog(
        user_id="SYSTEM_ADMIN",
        module="Backup & Restore",
        action="CREATE_BACKUP",
        table_name="backups",
        new_value=f"Backup archive created: {zip_filename}",
        status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "status": "SUCCESS",
        "backup_file": zip_filename,
        "backup_path": zip_filepath,
        "timestamp": timestamp_str
    }

@router.post("/restore")
def restore_database_backup(payload: RestoreBackupSchema, db: Session = Depends(get_db)):
    """
    Part 12 Restore System:
    Mandatory Owner PIN verification required before restoring database.
    """
    # 1. Verify Owner PIN
    owner = db.query(User).filter(User.owner_pin_hash.isnot(None)).first()
    if owner:
        if not verify_owner_pin(payload.owner_pin, owner.owner_pin_hash):
            raise HTTPException(status_code=403, detail="Owner PIN Verification Failed! Invalid PIN.")

    target_zip = os.path.join(BACKUP_DIR, payload.backup_file_name)
    if not os.path.exists(target_zip):
        raise HTTPException(status_code=404, detail=f"Backup archive {payload.backup_file_name} not found.")

    # 2. Extract Archive
    with zipfile.ZipFile(target_zip, 'r') as zipf:
        zipf.extractall("./")

    audit = AuditLog(
        user_id=payload.performed_by,
        module="Backup & Restore",
        action="RESTORE_BACKUP",
        table_name="backups",
        new_value=f"Restored database from archive: {payload.backup_file_name}",
        status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"Database successfully restored from {payload.backup_file_name}"
    }

@router.get("/list")
def list_backups():
    """Lists all available backup archives."""
    files = []
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.endswith(".zip"):
                fp = os.path.join(BACKUP_DIR, f)
                files.append({
                    "file_name": f,
                    "size_bytes": os.path.getsize(fp),
                    "created_time": datetime.fromtimestamp(os.path.getmtime(fp)).isoformat()
                })
    return {"backups": files}
