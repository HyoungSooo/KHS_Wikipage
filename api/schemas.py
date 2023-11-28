from ninja.schema import Schema
from datetime import datetime
from typing import List


class PostOut(Schema):
    id: int
    title: str
    created_at: datetime


class Message(Schema):
    message: str


class BasePostDetail(Schema):
    id: int
    title: str
    created_at: datetime


class PostDetail(Schema):
    id: int
    title: str
    content: str
    created_at: datetime
    rel_post: List[BasePostDetail]


class PostCreate(Schema):
    title: str
    content: str
