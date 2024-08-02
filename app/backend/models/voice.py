from pydantic import BaseModel
from models.chat_history import ChatHistory
from models.profile import Profile
from models.source import Source
from typing import List, Optional


class VoiceRequest(BaseModel):
    chat_history: Optional[List[ChatHistory]]
    profile: Profile


class VoiceResponse(BaseModel):
    response_message: str
    query_message: str
    sources: List[Source]
    additional_question_1: Optional[str]
    additional_question_2: Optional[str]
