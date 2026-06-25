from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.routes import earthquakes, metrics, reports
from src.config.logging import configure_logging, get_logger
from src.config.settings import get_settings
from src.database.indexes import ensure_indexes
from src.database.mongodb import close_client, get_database

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    db = get_database()
    await ensure_indexes(db)
    logger.info("API iniciada y conectada a MongoDB")
    yield
    await close_client()
    logger.info("API detenida")


app = FastAPI(
    title="Quipux Earthquake Events API",
    description="Plataforma de procesamiento de eventos sismicos en tiempo real (USGS).",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/prometheus-metrics", include_in_schema=False)

app.include_router(earthquakes.router)
app.include_router(metrics.router)
app.include_router(reports.router)


@app.get("/health", include_in_schema=False)
async def health():
    db = get_database()
    await db.command("ping")
    return {"status": "ok"}
