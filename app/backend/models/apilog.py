from typing import List

from models.source import SourceWithChunk
from pydantic import BaseModel


class APILog(BaseModel):
    user_query: str = ""
    response_message: str = ""
    retrieved_sources: List[SourceWithChunk] = []
    token_count: int = -1
