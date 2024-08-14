from pydantic import BaseModel


class Profile(BaseModel):
    profile_type: str
    # language: Literal["english", "chinese", "malay", "tamil", "default"]
    user_age: int
    user_gender: str
    user_condition: str
