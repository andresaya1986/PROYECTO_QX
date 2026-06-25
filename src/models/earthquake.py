from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class EarthquakeBase(BaseModel):
    event_id: str
    magnitude: float
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: datetime

    @field_validator("event_time")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class EarthquakeCreate(EarthquakeBase):
    """Modelo interno producido por processing_service a partir del GeoJSON de USGS."""


class EarthquakeOut(EarthquakeBase):
    id: str = Field(alias="_id")
    magnitude_range: str

    model_config = {"populate_by_name": True}


class USGSFeatureProperties(BaseModel):
    mag: float | None = None
    place: str | None = None
    time: int


class USGSFeatureGeometry(BaseModel):
    coordinates: list[float]


class USGSFeature(BaseModel):
    id: str
    properties: USGSFeatureProperties
    geometry: USGSFeatureGeometry


class USGSFeedResponse(BaseModel):
    features: list[USGSFeature] = Field(default_factory=list)
