from typing import List, Optional

from models.chat_history import ChatHistory
from models.profile import Profile
from pydantic import BaseModel


class Request(BaseModel):
    chat_history: Optional[List[ChatHistory]]
    profile: Optional[Profile]
    query: dict[str, str]
    language: str
