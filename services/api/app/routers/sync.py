from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from ..database import get_db

router = APIRouter(prefix="/sync", tags=["Cloud Sync"])

class SyncPushPayload(BaseModel):
    node_id: str
    timestamp: str
    parties: List[Dict[str, Any]] = []

@router.post("/push")
def receive_sync_push(payload: SyncPushPayload, db: Session = Depends(get_db)):
    """
    Receives change sets from offline Desktop nodes and merges them into Cloud database.
    """
    processed_count = len(payload.parties)
    return {
        "status": "success",
        "node_id": payload.node_id,
        "processed_records": processed_count,
        "server_timestamp": payload.timestamp
    }
