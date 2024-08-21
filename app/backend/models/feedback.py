from typing import List, Literal

from models.chat_history import ChatHistory
from pydantic import BaseModel


class Feedback(BaseModel):
    chat_history: List[ChatHistory]
    response: Literal["positive", "negative"]
