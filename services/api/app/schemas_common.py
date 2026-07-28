from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """
    Part 11 Standardized API Response Format:
    Every API response contains: success, message, data, errors, timestamp.
    """
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[Any] = None
    timestamp: str = datetime.utcnow().isoformat() + "Z"
