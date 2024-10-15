from pydantic import BaseModel


class Account(BaseModel):
    username: str
    password: str
