from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageModel(BaseModel):
    conversation_id: str
    sender_id: str
    text: str
    timestamp: Optional[datetime] = None