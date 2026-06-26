from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from .object import validate_object_id


class LayerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    categories: list[str] = []
    order: int = 0


class Package(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    entry_points: list[str] = []
    default_layout: str = "layered"
    layers: list[LayerConfig] = []
    theme: str = "blue"
    keywords: list[str] = []
    dir_name: str = ""

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        return validate_object_id(v)

    @field_validator("entry_points")
    @classmethod
    def _validate_entry_points(cls, v: list[str]) -> list[str]:
        for eid in v:
            validate_object_id(eid)
        return v

    def ordered_layers(self) -> list[LayerConfig]:
        return sorted(self.layers, key=lambda l: l.order)
