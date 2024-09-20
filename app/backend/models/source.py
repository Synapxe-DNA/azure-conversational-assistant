from typing import List

from pydantic import BaseModel


class Source(BaseModel):
    ids: List[str]
    title: str
    cover_image_url: str
    full_url: str
    content_category: str
    category_description: str
    pr_name: str
    date_modified: str


class SourceWithChunk(BaseModel):
    id: str
    title: str
    cover_image_url: str
    full_url: str
    content_category: str
    category_description: str
    pr_name: str
    date_modified: str
    chunk: str
