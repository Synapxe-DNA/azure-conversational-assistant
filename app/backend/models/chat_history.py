from typing import List

from models.chat_message import ChatMessageWithSource
from pydantic import BaseModel


class ChatHistory(BaseModel):
    id: str
    session_id: str
    created_at: str
    last_modified: str
    chat_messages: List[ChatMessageWithSource]

