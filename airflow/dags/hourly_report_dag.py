import asyncio
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from motor.motor_asyncio import AsyncIOMotorClient

from src.config.settings import get_settings
from src.database.repositories import EarthquakeRepository, ReportRepository
from src.services.reporting_service import ReportingService


def _hour_window(data_interval_start: datetime) -> tuple[datetime, datetime]:
    hour_start = data_interval_start.replace(minute=0, second=0, microsecond=0)
    return hour_start, hour_start + timedelta(hours=1)


async def _extract_events(hour_start: datetime, hour_end: datetime) -> list[dict]:
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_uri)
    try:
        repo = EarthquakeRepository(client[settings.mongo_db_name])
        service = ReportingService(earthquake_repo=repo)
        return await service.fetch_window_events(hour_start, hour_end)
    finally:
        client.close()


async def _persist_report(report: dict) -> None:
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_uri)
    try:
        repo = ReportRepository(client[settings.mongo_db_name])
        service = ReportingService(report_repo=repo)
        await service.persist_report(report)
    finally:
        client.close()


@dag(
    dag_id="hourly_report_dag",
    description="Genera el reporte consolidado horario de sismos a partir de la coleccion earthquakes",
    schedule="0 * * * *",
    start_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["quipux", "earthquakes"],
)
def hourly_report_dag():
    @task
    def extract_events(data_interval_start=None, **_) -> dict:
        hour_start, hour_end = _hour_window(data_interval_start)
        events = asyncio.run(_extract_events(hour_start, hour_end))
        return {"hour_start": hour_start.isoformat(), "events": events}

    @task
    def generate_report(payload: dict) -> dict:
        hour_start = datetime.fromisoformat(payload["hour_start"])
        report = ReportingService.compute_report(payload["events"], hour_start)
        report["report_date"] = report["report_date"].isoformat()
        return report

    @task
    def persist_report(report: dict) -> None:
        report = dict(report)
        report["report_date"] = datetime.fromisoformat(report["report_date"])
        asyncio.run(_persist_report(report))

    persist_report(generate_report(extract_events()))


hourly_report_dag()
