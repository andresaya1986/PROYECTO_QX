from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.deps import get_metrics_repo
from src.database.repositories import MetricsRepository
from src.utils.cache import ttl_cache

router = APIRouter(tags=["metrics"])


class MetricsFilters(BaseModel):
    window: str | None = Field(default=None, description="Ventana horaria, formato YYYY-MM-DDTHH")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


def _serialize(doc: dict) -> dict:
    count = doc.get("earthquake_count", 0)
    sum_magnitude = doc.get("sum_magnitude", 0.0)
    return {
        "window": doc["window"],
        "earthquake_count": count,
        "avg_magnitude": round(sum_magnitude / count, 3) if count else 0.0,
        "max_magnitude": doc.get("max_magnitude", 0.0),
        "magnitude_distribution": doc.get("magnitude_distribution", {}),
    }


@ttl_cache()
async def _fetch_one(repo: MetricsRepository, window: str) -> dict | None:
    return await repo.find_one(window)


@ttl_cache()
async def _fetch_latest(repo: MetricsRepository) -> dict | None:
    return await repo.find_latest()


@ttl_cache()
async def _fetch_many(repo: MetricsRepository, skip: int, limit: int) -> list[dict]:
    return await repo.find_many(skip=skip, limit=limit)


@router.get("/metrics")
async def get_metrics(
    filters: Annotated[MetricsFilters, Query()],
    repo: MetricsRepository = Depends(get_metrics_repo),
):
    if filters.window:
        doc = await _fetch_one(repo, filters.window)
        if doc is None:
            raise HTTPException(status_code=404, detail="No hay metricas para esa ventana")
        return _serialize(doc)

    skip = (filters.page - 1) * filters.page_size
    docs = await _fetch_many(repo, skip, filters.page_size)
    if not docs:
        latest = await _fetch_latest(repo)
        return {"items": [_serialize(latest)] if latest else []}

    return {"items": [_serialize(doc) for doc in docs], "page": filters.page, "page_size": filters.page_size}
