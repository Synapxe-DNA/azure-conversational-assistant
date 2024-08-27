from pydantic import BaseModel


class ChatHistory(BaseModel):
    role: str
    content: str
