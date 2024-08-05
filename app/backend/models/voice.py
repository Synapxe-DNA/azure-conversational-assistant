from typing import List, Optional

from models.chat_history import ChatHistory
from models.profile import Profile
from models.source import Source
from pydantic import BaseModel


class VoiceRequest(BaseModel):
    chat_history: Optional[List[ChatHistory]]
    profile: Optional[Profile]
    query: bytes


class VoiceResponse(BaseModel):
    response_message: str
    query_message: str
    audio_base64: str
    sources: List[Source]
    additional_question_1: Optional[str]
    additional_question_2: Optional[str]
    audio_base64: str
