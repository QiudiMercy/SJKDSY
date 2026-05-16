from pydantic import BaseModel
from typing import Optional, List

class SendMessageRequest(BaseModel):
    game_uid: str
    content: str

class ChatReplyResponse(BaseModel):
    reply: str
    is_system_reply: bool
    system_reply: Optional[str] = None
    new_status: Optional[dict] = None

class MessageItem(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    messages: List[MessageItem]