from typing import List

from models.chat_message import ChatMessageWithSource
from pydantic import BaseModel


class ChatHistory(BaseModel):
    id: str
    session_id: str
    first_message_date: str
    lastest_message_date: str
    chat_messages: List[ChatMessageWithSource]
