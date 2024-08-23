from typing import List

from pydantic import BaseModel


class Source(BaseModel):
    id: List[str]
    title: str
    cover_image_url: str
    full_url: str
    content_category: str
