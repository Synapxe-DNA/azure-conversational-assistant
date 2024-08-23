from typing import List, Optional

from models.chat_history import ChatHistory
from models.profile import Profile
from models.source import Source
from pydantic import BaseModel


class VoiceChatRequest(BaseModel):
    chat_history: Optional[List[ChatHistory]]
    profile: Optional[Profile]
    query: str


class VoiceChatResponse(BaseModel):
    response_message: str
    audio_base64: str
    sources: List[Source]
