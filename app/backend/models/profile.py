from pydantic import BaseModel

class Profile(BaseModel):
    profile_type: str
    user_age: int
    user_gender: str
    user_condition: str
