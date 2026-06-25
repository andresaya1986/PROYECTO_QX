from collections import Counter
from datetime import datetime

from src.database.repositories import EarthquakeRepository, ReportRepository


def extract_region(location: str) -> str:
    """Aproxima la región/estado/país a partir del string de ubicación de USGS.

    Los strings de USGS suelen tener la forma "20 km NW of California" o
    "39 km SSW of Nanwalek, Alaska". Se usa el último segmento tras la coma,
    o tras " of " si no hay coma, como aproximación de la región (definida
    por el candidato, no provista por la API).
    """
    if "," in location:
        return location.rsplit(",", 1)[1].strip()
    if " of " in location:
        return location.rsplit(" of ", 1)[1].strip()
    return location.strip()


class ReportingService:
    """Genera el reporte consolidado horario. Expone pasos separados (leer/generar/persistir)
    para que el DAG de Airflow pueda representarlos como tasks independientes."""

    def __init__(
        self,
        earthquake_repo: EarthquakeRepository | None = None,
        report_repo: ReportRepository | None = None,
    ) -> None:
        self._earthquake_repo = earthquake_repo
        self._report_repo = report_repo

    async def fetch_window_events(self, hour_start: datetime, hour_end: datetime) -> list[dict]:
        events = await self._earthquake_repo.find_between(hour_start, hour_end)
        return [
            {"magnitude": e["magnitude"], "location": e["location"]}
            for e in events
        ]

    @staticmethod
    def compute_report(events: list[dict], hour_start: datetime, top_n: int = 3) -> dict:
        total_events = len(events)
        magnitudes = [e["magnitude"] for e in events]
        average_magnitude = round(sum(magnitudes) / total_events, 3) if total_events else 0.0
        max_magnitude = max(magnitudes) if magnitudes else 0.0

        region_counts = Counter(extract_region(e["location"]) for e in events)
        top_locations = [region for region, _ in region_counts.most_common(top_n)]

        return {
            "report_date": hour_start,
            "total_events": total_events,
            "average_magnitude": average_magnitude,
            "max_magnitude": max_magnitude,
            "top_locations": top_locations,
        }

    async def persist_report(self, report: dict) -> None:
        await self._report_repo.upsert_report(report)

    async def build_hourly_report(self, hour_start: datetime, hour_end: datetime, top_n: int = 3) -> dict:
        events = await self.fetch_window_events(hour_start, hour_end)
        report = self.compute_report(events, hour_start, top_n)
        await self.persist_report(report)
        return report
