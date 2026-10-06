from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from services.minio_service import get_minio_service

def _to_url(name: str) -> str:
    return get_minio_service().build_url(name)


MediaUrl = Annotated[str, AfterValidator(_to_url)]


class PeriodTile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    days_count: int
    image_url: MediaUrl
    likes_count: int
    is_mine: Literal[0, 1]


class PeriodFeed(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    order_number: int
    days_count: int
    video_url: MediaUrl
    likes_count: int
    is_liked: Literal[0, 1]

class PeriodDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    order_number: int | None
    days_count: int | None
    image_url: MediaUrl
    video_url: MediaUrl


class LikeOut(BaseModel):
    likes_count: int


class PeriodPublish(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1, max_length=500)
    order_number: int = Field(ge=1)
    days_count: int = Field(ge=1, le=366)


class LikeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    like: Literal[0, 1]
