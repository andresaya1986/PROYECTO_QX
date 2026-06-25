from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING, ReturnDocument

from src.config.constants import (
    EARTHQUAKES_COLLECTION,
    HOURLY_REPORTS_COLLECTION,
    METRICS_COLLECTION,
)
from src.models.earthquake import EarthquakeCreate


class EarthquakeRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[EARTHQUAKES_COLLECTION]

    async def upsert(self, earthquake: EarthquakeCreate) -> bool:
        """Inserta el evento si no existe. Devuelve True si fue un evento nuevo."""
        result = await self._collection.update_one(
            {"event_id": earthquake.event_id},
            {"$setOnInsert": earthquake.model_dump()},
            upsert=True,
        )
        return result.upserted_id is not None

    async def find_many(
        self,
        min_magnitude: float | None = None,
        max_magnitude: float | None = None,
        location: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        sort_by: str = "event_time",
        order: int = DESCENDING,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        magnitude_filter: dict[str, float] = {}
        if min_magnitude is not None:
            magnitude_filter["$gte"] = min_magnitude
        if max_magnitude is not None:
            magnitude_filter["$lte"] = max_magnitude
        if magnitude_filter:
            query["magnitude"] = magnitude_filter

        time_filter: dict[str, datetime] = {}
        if start_time is not None:
            time_filter["$gte"] = start_time
        if end_time is not None:
            time_filter["$lte"] = end_time
        if time_filter:
            query["event_time"] = time_filter

        if location:
            query["location"] = {"$regex": location, "$options": "i"}

        cursor = (
            self._collection.find(query)
            .sort(sort_by, order)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def count(
        self,
        min_magnitude: float | None = None,
        max_magnitude: float | None = None,
        location: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        query: dict[str, Any] = {}
        magnitude_filter: dict[str, float] = {}
        if min_magnitude is not None:
            magnitude_filter["$gte"] = min_magnitude
        if max_magnitude is not None:
            magnitude_filter["$lte"] = max_magnitude
        if magnitude_filter:
            query["magnitude"] = magnitude_filter

        time_filter: dict[str, datetime] = {}
        if start_time is not None:
            time_filter["$gte"] = start_time
        if end_time is not None:
            time_filter["$lte"] = end_time
        if time_filter:
            query["event_time"] = time_filter

        if location:
            query["location"] = {"$regex": location, "$options": "i"}

        return await self._collection.count_documents(query)

    async def find_between(self, start_time: datetime, end_time: datetime) -> list[dict[str, Any]]:
        cursor = self._collection.find(
            {"event_time": {"$gte": start_time, "$lt": end_time}}
        )
        return [doc async for doc in cursor]


class MetricsRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[METRICS_COLLECTION]

    async def apply_event(self, window: str, magnitude: float, magnitude_range: str) -> dict[str, Any]:
        update = {
            "$inc": {
                "earthquake_count": 1,
                "sum_magnitude": magnitude,
                f"magnitude_distribution.{magnitude_range}": 1,
            },
            "$max": {"max_magnitude": magnitude},
            "$setOnInsert": {"window": window},
        }
        return await self._collection.find_one_and_update(
            {"window": window},
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def find_one(self, window: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"window": window})

    async def find_latest(self) -> dict[str, Any] | None:
        return await self._collection.find_one(sort=[("window", DESCENDING)])

    async def find_many(self, skip: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        cursor = (
            self._collection.find({})
            .sort("window", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]


class ReportRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[HOURLY_REPORTS_COLLECTION]

    async def upsert_report(self, report: dict[str, Any]) -> None:
        await self._collection.update_one(
            {"report_date": report["report_date"]},
            {"$set": report},
            upsert=True,
        )

    async def find_many(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
        order: int = DESCENDING,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        date_filter: dict[str, datetime] = {}
        if start_date is not None:
            date_filter["$gte"] = start_date
        if end_date is not None:
            date_filter["$lte"] = end_date
        if date_filter:
            query["report_date"] = date_filter

        cursor = (
            self._collection.find(query)
            .sort("report_date", order)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]
