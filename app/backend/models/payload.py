import datetime
from typing import Optional

from pydantic import BaseModel


class Payload(BaseModel):
    username: str
    password: str
    exp: Optional[datetime.datetime] = None
