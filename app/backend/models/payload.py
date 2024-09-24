import datetime

from pydantic import BaseModel


class Payload(BaseModel):
    username: str
    exp: datetime.datetime
