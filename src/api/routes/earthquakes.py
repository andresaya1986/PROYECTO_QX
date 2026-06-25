from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING

from src.api.deps import get_earthquake_repo
from src.config.constants import classify_magnitude
from src.database.repositories import EarthquakeRepository

router = APIRouter(tags=["earthquakes"])


class EarthquakeFilters(BaseModel):
    min_magnitude: float | None = Field(default=None, ge=-10, le=10)
    max_magnitude: float | None = Field(default=None, ge=-10, le=10)
    location: str | None = Field(default=None, max_length=200)
    start_time: datetime | None = None
    end_time: datetime | None = None
    sort_by: Literal["event_time", "magnitude"] = "event_time"
    order: Literal["asc", "desc"] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "event_id": doc["event_id"],
        "magnitude": doc["magnitude"],
        "magnitude_range": classify_magnitude(doc["magnitude"]),
        "location": doc["location"],
        "latitude": doc["latitude"],
        "longitude": doc["longitude"],
        "depth": doc["depth"],
        "event_time": doc["event_time"],
    }


@router.get("/earthquakes")
async def list_earthquakes(
    filters: Annotated[EarthquakeFilters, Query()],
    repo: EarthquakeRepository = Depends(get_earthquake_repo),
):
    order = DESCENDING if filters.order == "desc" else ASCENDING
    skip = (filters.page - 1) * filters.page_size

    docs = await repo.find_many(
        min_magnitude=filters.min_magnitude,
        max_magnitude=filters.max_magnitude,
        location=filters.location,
        start_time=filters.start_time,
        end_time=filters.end_time,
        sort_by=filters.sort_by,
        order=order,
        skip=skip,
        limit=filters.page_size,
    )
    total = await repo.count(
        min_magnitude=filters.min_magnitude,
        max_magnitude=filters.max_magnitude,
        location=filters.location,
        start_time=filters.start_time,
        end_time=filters.end_time,
    )

    return {
        "items": [_serialize(doc) for doc in docs],
        "page": filters.page,
        "page_size": filters.page_size,
        "total": total,
    }
