import asyncio
import signal

from prometheus_client import start_http_server

from src.clients.usgs_client import USGSClient
from src.config.logging import configure_logging, get_logger
from src.config.settings import get_settings
from src.database.indexes import ensure_indexes
from src.database.mongodb import close_client, get_database
from src.database.repositories import EarthquakeRepository, MetricsRepository
from src.services.ingestion_service import IngestionService
from src.services.metrics_service import MetricsService
from src.utils.metrics import (
    earthquakes_duplicates_total,
    earthquakes_ingested_total,
    ingestion_cycle_duration_seconds,
    ingestion_errors_total,
)

logger = get_logger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    start_http_server(settings.ingestion_metrics_port)
    logger.info(
        "Servidor de metricas Prometheus iniciado",
        extra={"extra_fields": {"port": settings.ingestion_metrics_port}},
    )

    db = get_database()
    await ensure_indexes(db)

    earthquake_repo = EarthquakeRepository(db)
    metrics_repo = MetricsRepository(db)
    metrics_service = MetricsService(metrics_repo)
    usgs_client = USGSClient(settings.usgs_api_url)
    ingestion_service = IngestionService(usgs_client, earthquake_repo, metrics_service)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_event.set)

    logger.info(
        "Iniciando worker de ingesta",
        extra={"extra_fields": {"interval_seconds": settings.ingestion_interval_seconds}},
    )

    while not stop_event.is_set():
        with ingestion_cycle_duration_seconds.time():
            try:
                result = await ingestion_service.run_cycle()
                earthquakes_ingested_total.inc(result.new_events)
                earthquakes_duplicates_total.inc(result.duplicates)
            except Exception:
                ingestion_errors_total.inc()
                logger.exception("Error en el ciclo de ingesta")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.ingestion_interval_seconds)
        except asyncio.TimeoutError:
            pass

    await close_client()
    logger.info("Worker de ingesta detenido")


if __name__ == "__main__":
    asyncio.run(main())
