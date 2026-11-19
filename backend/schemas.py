from typing import Literal

import pycountry
from pydantic import BaseModel, Field, field_validator

from backend.config import settings


class CreateCampaign(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo: list[str] = Field(min_length=1)
    offer_id: int = Field(gt=0)
    domain_id: int = Field(gt=0)
    group_id: int = Field(gt=0)
    traffic_source_id: int = Field(gt=0)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Введите название кампании")
        prefix = settings().campaign_name_prefix
        if not value.startswith(prefix):
            value = prefix + value
        if not value.removeprefix(prefix).strip():
            raise ValueError("Введите название после префикса кампании")
        if len(value) > 255:
            raise ValueError("Название вместе с префиксом должно содержать не более 255 символов")
        return value

    @field_validator("geo")
    @classmethod
    def valid_geo(cls, values: list[str]) -> list[str]:
        values = list(dict.fromkeys(x.strip().upper() for x in values))
        if any(pycountry.countries.get(alpha_2=x) is None for x in values):
            raise ValueError("Используйте ISO-коды стран: AU, MX, RO")
        return values


class EditOffer(BaseModel):
    revision: int = Field(gt=0)
    action: Literal["add", "remove", "restore", "pin", "unpin"]
    offer_id: int = Field(gt=0)
    share: int | None = Field(default=None, ge=0, le=100, strict=True)


class Revision(BaseModel):
    revision: int = Field(gt=0)


class FetchRequest(BaseModel):
    discard_drafts: bool = False
    revisions: dict[int, int] = Field(default_factory=dict)
