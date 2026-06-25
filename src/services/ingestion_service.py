from dataclasses import dataclass

from src.clients.usgs_client import USGSClient
from src.config.logging import get_logger
from src.database.repositories import EarthquakeRepository
from src.services.metrics_service import MetricsService
from src.services.processing_service import transform_feature

logger = get_logger(__name__)


@dataclass
class IngestionCycleResult:
    fetched: int = 0
    new_events: int = 0
    duplicates: int = 0
    skipped: int = 0


class IngestionService:
    """Orquesta un ciclo de ingesta: fetch -> transform -> dedupe -> persistencia -> métricas."""

    def __init__(
        self,
        usgs_client: USGSClient,
        earthquake_repo: EarthquakeRepository,
        metrics_service: MetricsService,
    ) -> None:
        self._usgs_client = usgs_client
        self._earthquake_repo = earthquake_repo
        self._metrics_service = metrics_service

    async def run_cycle(self) -> IngestionCycleResult:
        result = IngestionCycleResult()
        try:
            feed = await self._usgs_client.fetch_recent_earthquakes()
        except Exception:
            logger.exception("Fallo al consultar la API de USGS")
            raise

        result.fetched = len(feed.features)

        for feature in feed.features:
            earthquake = transform_feature(feature)
            if earthquake is None:
                result.skipped += 1
                continue

            is_new = await self._earthquake_repo.upsert(earthquake)
            if not is_new:
                result.duplicates += 1
                continue

            result.new_events += 1
            await self._metrics_service.record_event(earthquake)

        logger.info(
            "Ciclo de ingesta completado",
            extra={
                "extra_fields": {
                    "fetched": result.fetched,
                    "new_events": result.new_events,
                    "duplicates": result.duplicates,
                    "skipped": result.skipped,
                }
            },
        )
        return result
