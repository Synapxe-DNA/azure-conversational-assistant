from pydantic import BaseModel

class Source(BaseModel):
    title: str
    url: str
    meta_description: str
    image_url: str
