from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None

class HelloResponse(BaseModel):
    message: str
    status: str
    timestamp: datetime
    OPENAI_API_KEY_SECRET_NAME: str
    AWS_REGION_NAME: str

class ConversationItem(BaseModel):
    conversation_id: str
    user_id: str
    title: str
    created_at: datetime
    last_updated_at: datetime
    latest_response_id: Optional[str] = None

class ConversationResponse(BaseModel):
    items: List[ConversationItem]
