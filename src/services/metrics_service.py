from src.config.constants import classify_magnitude
from src.database.repositories import MetricsRepository
from src.models.earthquake import EarthquakeCreate


class MetricsService:
    """Mantiene los agregados por ventana horaria mediante upserts atómicos."""

    def __init__(self, metrics_repo: MetricsRepository) -> None:
        self._metrics_repo = metrics_repo

    @staticmethod
    def window_for(earthquake: EarthquakeCreate) -> str:
        return earthquake.event_time.strftime("%Y-%m-%dT%H")

    async def record_event(self, earthquake: EarthquakeCreate) -> dict:
        window = self.window_for(earthquake)
        magnitude_range = classify_magnitude(earthquake.magnitude)
        return await self._metrics_repo.apply_event(window, earthquake.magnitude, magnitude_range)
