import httpx

from src.config.logging import get_logger
from src.models.earthquake import USGSFeedResponse

logger = get_logger(__name__)


class USGSClient:
    """Cliente HTTP para el feed GeoJSON de terremotos del USGS Earthquake Program."""

    def __init__(self, api_url: str, timeout_seconds: float = 10.0) -> None:
        self._api_url = api_url
        self._timeout_seconds = timeout_seconds

    async def fetch_recent_earthquakes(self) -> USGSFeedResponse:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(self._api_url)
            response.raise_for_status()
            return USGSFeedResponse.model_validate(response.json())
