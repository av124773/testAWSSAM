from pydantic import BaseModel
from typing import Optional

class MessageRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None
