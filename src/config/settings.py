from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_user: str = "quipux"
    mongo_password: str = "change-me"
    mongo_host: str = "mongodb"
    mongo_port: int = 27017
    mongo_db_name: str = "earthquakes_db"

    usgs_api_url: str = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    )
    ingestion_interval_seconds: int = 180

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    cache_ttl_seconds: int = 30

    ingestion_metrics_port: int = 9100

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/?authSource=admin"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
