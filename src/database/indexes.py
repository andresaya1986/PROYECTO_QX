from motor.motor_asyncio import AsyncIOMotorDatabase

from src.config.constants import (
    EARTHQUAKES_COLLECTION,
    HOURLY_REPORTS_COLLECTION,
    METRICS_COLLECTION,
)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    earthquakes = db[EARTHQUAKES_COLLECTION]
    await earthquakes.create_index("event_id", unique=True, name="uniq_event_id")
    await earthquakes.create_index([("event_time", -1)], name="event_time_desc")
    await earthquakes.create_index(
        [("magnitude", 1), ("event_time", -1)], name="magnitude_event_time"
    )

    metrics = db[METRICS_COLLECTION]
    await metrics.create_index("window", unique=True, name="uniq_window")

    reports = db[HOURLY_REPORTS_COLLECTION]
    await reports.create_index([("report_date", -1)], name="report_date_desc")
