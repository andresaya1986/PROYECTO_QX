from datetime import datetime, timezone

from src.config.logging import get_logger
from src.models.earthquake import EarthquakeCreate, USGSFeature

logger = get_logger(__name__)


def transform_feature(feature: USGSFeature) -> EarthquakeCreate | None:
    """Convierte un feature GeoJSON de USGS al modelo interno. Devuelve None si faltan datos clave."""
    props = feature.properties
    if props.mag is None:
        logger.warning("Evento sin magnitud descartado", extra={"extra_fields": {"event_id": feature.id}})
        return None

    coordinates = feature.geometry.coordinates
    if len(coordinates) < 3:
        logger.warning("Evento sin coordenadas completas descartado", extra={"extra_fields": {"event_id": feature.id}})
        return None

    longitude, latitude, depth = coordinates[0], coordinates[1], coordinates[2]
    event_time = datetime.fromtimestamp(props.time / 1000, tz=timezone.utc)

    return EarthquakeCreate(
        event_id=feature.id,
        magnitude=props.mag,
        location=props.place or "unknown",
        latitude=latitude,
        longitude=longitude,
        depth=depth,
        event_time=event_time,
    )
