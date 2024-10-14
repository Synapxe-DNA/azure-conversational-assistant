from typing import List

from models.request import Request
from models.source import Source, SourceWithChunk
from pydantic import BaseModel


class TextChatRequest(Request):
    pass


class TextChatResponse(BaseModel):
    response_message: str
    sources: List[Source]


class TextChatResponseWithChunk(BaseModel):
    response_message: str
    sources: List[SourceWithChunk]
