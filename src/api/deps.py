from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.database.mongodb import get_database
from src.database.repositories import EarthquakeRepository, MetricsRepository, ReportRepository


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


# Los repositorios envuelven la misma conexion (pool) singleton de Motor;
# se cachean para que las claves de cache TTL en las rutas (que incluyen
# la instancia del repositorio) sean estables entre requests.
@lru_cache
def get_earthquake_repo() -> EarthquakeRepository:
    return EarthquakeRepository(get_db())


@lru_cache
def get_metrics_repo() -> MetricsRepository:
    return MetricsRepository(get_db())


@lru_cache
def get_report_repo() -> ReportRepository:
    return ReportRepository(get_db())
