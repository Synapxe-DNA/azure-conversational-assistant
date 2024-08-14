from typing import List, Literal

from pydantic import BaseModel
from models.chat_history import ChatHistory


class Feedback(BaseModel):
    chat_history: List[ChatHistory]
    response: Literal["positive", "negative"]
