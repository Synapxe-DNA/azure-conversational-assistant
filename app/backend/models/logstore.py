from typing import List

from models.source import SourceWithChunk
from pydantic import BaseModel


class LogStore(BaseModel):
    date_time: str = ""
    user_query: str = ""
    response_message: str = ""
    status: int = -1
    retrieved_sources: List[SourceWithChunk] = []
    token_count: int = -1
    time_taken: float = -1.0
