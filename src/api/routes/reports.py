from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING

from src.api.deps import get_report_repo
from src.database.repositories import ReportRepository
from src.utils.cache import ttl_cache

router = APIRouter(tags=["reports"])


class ReportFilters(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    order: Literal["asc", "desc"] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


def _serialize(doc: dict) -> dict:
    return {
        "report_date": doc["report_date"],
        "total_events": doc["total_events"],
        "average_magnitude": doc["average_magnitude"],
        "max_magnitude": doc["max_magnitude"],
        "top_locations": doc.get("top_locations", []),
    }


@ttl_cache()
async def _fetch_reports(
    repo: ReportRepository,
    start_date: datetime | None,
    end_date: datetime | None,
    order: int,
    skip: int,
    limit: int,
) -> list[dict]:
    return await repo.find_many(
        start_date=start_date, end_date=end_date, skip=skip, limit=limit, order=order
    )


@router.get("/reports")
async def list_reports(
    filters: Annotated[ReportFilters, Query()],
    repo: ReportRepository = Depends(get_report_repo),
):
    order = DESCENDING if filters.order == "desc" else ASCENDING
    skip = (filters.page - 1) * filters.page_size
    docs = await _fetch_reports(repo, filters.start_date, filters.end_date, order, skip, filters.page_size)
    return {
        "items": [_serialize(doc) for doc in docs],
        "page": filters.page,
        "page_size": filters.page_size,
    }
