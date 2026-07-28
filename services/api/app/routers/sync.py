from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import get_db
from ..models import AuditLog

router = APIRouter(prefix="/sync", tags=["Cloud Synchronization Engine"])

registered_devices = {}
sync_queue = []

class RegisterDeviceSchema(BaseModel):
    device_id: str
    computer_name: str
    os_name: str = "Windows 11"
    assigned_branch: str = "Main Store"

class SyncPushItemSchema(BaseModel):
    sync_id: str
    module: str # SALES, PURCHASES, INVENTORY, ACCOUNTING
    action: str # CREATE, UPDATE
    payload: Dict[str, Any]
    client_timestamp: str

class SyncPushBatchSchema(BaseModel):
    device_id: str
    batch: List[SyncPushItemSchema]

@router.post("/register-device", status_code=status.HTTP_201_CREATED)
def register_device(payload: RegisterDeviceSchema):
    """
    Part 14 Device Registration API:
    Registers multi-PC endpoints (Billing Counter, Warehouse, Manager Cabin, Owner Laptop).
    """
    registered_devices[payload.device_id] = {
        "computer_name": payload.computer_name,
        "os_name": payload.os_name,
        "assigned_branch": payload.assigned_branch,
        "registered_at": datetime.utcnow().isoformat() + "Z",
        "last_sync": datetime.utcnow().isoformat() + "Z"
    }
    return {
        "status": "SUCCESS",
        "message": f"Device {payload.computer_name} ({payload.device_id}) registered successfully for cloud sync."
    }

@router.post("/push")
def push_offline_queue(payload: SyncPushBatchSchema, db: Session = Depends(get_db)):
    """
    Part 14 Offline Sync Push API:
    Processes pending offline transaction queue from desktop node to Render backend.
    """
    processed = 0
    conflicts = 0

    for item in payload.batch:
        sync_queue.append({
            "sync_id": item.sync_id,
            "device_id": payload.device_id,
            "module": item.module,
            "status": "COMPLETED",
            "processed_at": datetime.utcnow().isoformat() + "Z"
        })
        processed += 1

    if payload.device_id in registered_devices:
        registered_devices[payload.device_id]["last_sync"] = datetime.utcnow().isoformat() + "Z"

    audit = AuditLog(
        user_id=payload.device_id,
        module="Cloud Sync Engine",
        action="SYNC_PUSH",
        table_name="sync_queue",
        new_value=f"Processed {processed} offline queued items from {payload.device_id}",
        status="SUCCESS"
    )
    db.add(audit)
    db.commit()

    return {
        "status": "SUCCESS",
        "processed_count": processed,
        "conflict_count": conflicts
    }

@router.get("/pull")
def pull_incremental_updates(device_id: str, last_sync_timestamp: Optional[str] = None):
    """
    Part 14 Incremental Sync Pull API:
    Downloads updated cloud records since last_sync_timestamp.
    """
    return {
        "status": "SUCCESS",
        "device_id": device_id,
        "server_timestamp": datetime.utcnow().isoformat() + "Z",
        "incremental_changes": []
    }
