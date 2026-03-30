from pydantic import BaseModel, Field
from datetime import datetime


class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class PostResponse(BaseModel):
    post_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
