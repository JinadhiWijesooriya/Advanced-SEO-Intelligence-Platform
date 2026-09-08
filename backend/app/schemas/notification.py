from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    type: str
    message: str

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationInDBBase(NotificationBase):
    id: int
    user_id: int
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Notification(NotificationInDBBase):
    pass
