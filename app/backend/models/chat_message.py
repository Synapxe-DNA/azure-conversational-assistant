from typing import List

from models.source import Source, SourceWithChunk
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatMessageWithSource(BaseModel):
    role: str
    content: str
    sources: List[SourceWithChunk] | List[Source]
