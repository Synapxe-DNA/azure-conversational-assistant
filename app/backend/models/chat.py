from typing import List

from models.request import Request
from models.source import Source
from pydantic import BaseModel


class TextChatRequest(Request):
    pass


class TextChatResponse(BaseModel):
    response_message: str
    sources: List[Source]
