from typing import List, Optional

from models.chat_message import ChatMessage
from models.profile import Profile
from pydantic import BaseModel


class Request(BaseModel):
    chat_history: Optional[List[ChatMessage]]
    profile: Optional[Profile]
    query: ChatMessage
    language: str
