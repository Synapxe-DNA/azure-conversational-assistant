from typing import Optional

from pydantic import BaseModel


class Profile(BaseModel):
    profile_type: str
    user_age: Optional[int] = -1
    user_gender: Optional[str] = "male"
    user_condition: Optional[str] = ""
