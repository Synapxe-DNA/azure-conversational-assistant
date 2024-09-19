from pydantic import BaseModel
import datetime
from typing import Optional


class Payload(BaseModel):
    username: str
    password:str
    exp: Optional[datetime.datetime] = None
