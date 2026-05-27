from pydantic import BaseModel
from typing import Optional, List

class SendMessageRequest(BaseModel):
    game_uid: str
    content: str
    time_passed_min: int = 0

class ChatReplyResponse(BaseModel):
    reply: str
    is_system_reply: bool = False
    system_reply: Optional[str] = None
    new_status: Optional[dict] = None
    segments: Optional[List[str]] = None

class MessageItem(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    messages: List[MessageItem]