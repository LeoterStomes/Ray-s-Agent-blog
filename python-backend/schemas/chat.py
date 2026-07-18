from pydantic import BaseModel
from typing import Optional

#agent 新会话功能
class ChatSessionStartRequest(BaseModel):
    sessionTitle: Optional[str] = None         #默认新会话
    initialMessage: Optional[str] = None

class ChatStreamRequest(BaseModel):
    sessionId: str         #创建会话的 ID
    userMessage: str        #用户输入的内容
