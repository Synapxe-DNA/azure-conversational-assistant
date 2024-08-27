from typing import List, Literal, Optional

from models.chat_history import ChatHistory
from models.profile import Profile
from models.source import Source, SourceWithChunk
from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    date_time: str
    feedback_type: Literal["positive", "negative"]
    feedback_category: str
    feedback_remarks: Optional[str]
    user_profile: Profile
    chat_history: List[ChatHistory]
    retrieved_sources: List[Source]


class FeedbackStore(BaseModel):
    date_time: str
    feedback_type: Literal["positive", "negative"]
    feedback_category: str
    feedback_remarks: Optional[str]
    user_profile: Profile
    chat_history: List[ChatHistory]
    retrieved_sources: List[SourceWithChunk]
