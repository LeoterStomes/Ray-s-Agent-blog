from pydantic import BaseModel
from typing import Optional

class ChatSessionStartRequest(BaseModel):
    sessionTitle: Optional[str] = None
    initialMessage: Optional[str] = None

class ChatStreamRequest(BaseModel):
    sessionId: str
    userMessage: str
