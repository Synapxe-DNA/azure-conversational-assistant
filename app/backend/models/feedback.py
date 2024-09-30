from typing import List, Literal, Optional

from models.chat_message import ChatMessageWithSource
from models.profile import Profile
from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    date_time: str
    feedback_type: Literal["positive", "negative"]
    feedback_category: List[str]
    feedback_remarks: Optional[str]
    user_profile: Profile
    chat_history: List[ChatMessageWithSource]


class FeedbackStore(BaseModel):
    date_time: str
    feedback_type: Literal["positive", "negative"]
    feedback_category: List[str]
    feedback_remarks: Optional[str]
    user_profile: Profile
    chat_history: List[ChatMessageWithSource]
