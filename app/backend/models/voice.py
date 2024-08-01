from pydantic import BaseModel
from models.chat_history import ChatHistory
from models.profile import Profile
from models.source import Source
from typing import List


class VoiceRequest(BaseModel):
    chat_history: List[ChatHistory]
    profile: Profile


class VoiceResponse(BaseModel):
    message: str
    sources: List[Source]
    additional_question_1: str
    additional_question_2: str
