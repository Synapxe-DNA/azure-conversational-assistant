from typing import List, Optional

from models.chat_history import ChatHistory
from models.profile import Profile
from models.source import Source
from pydantic import BaseModel


class TextChatRequest(BaseModel):
    chat_history: Optional[List[ChatHistory]]
    profile: Optional[Profile]
    query: dict[str, str]


class TextChatResponse(BaseModel):
    response_message: str
    sources: List[Source]
