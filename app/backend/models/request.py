from typing import List

from models.chat_message import ChatMessage
from models.profile import Profile
from pydantic import BaseModel


class Request(BaseModel):
    chat_history: List[ChatMessage]
    profile: Profile
    query: ChatMessage
    language: str
