from typing import List

from models.source import Source, SourceWithChunk
from pydantic import BaseModel


class SpeechRequest(BaseModel):
    text: str
