from typing import List

from models.source import Source, SourceWithChunk
from pydantic import BaseModel


class ChatHistory(BaseModel):
    role: str
    content: str


class ChatHistoryWithSource(BaseModel):
    role: str
    content: str
    sources: List[SourceWithChunk] | List[Source]
