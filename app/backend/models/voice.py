from typing import List

from models.request import Request
from models.source import Source
from pydantic import BaseModel


class VoiceChatRequest(Request):
    pass


class VoiceChatResponse(BaseModel):
    response_message: str
    audio_base64: str
    sources: List[Source]
