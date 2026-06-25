from prometheus_client import Counter, Histogram

earthquakes_ingested_total = Counter(
    "earthquakes_ingested_total", "Total de eventos sismicos nuevos ingeridos"
)
earthquakes_duplicates_total = Counter(
    "earthquakes_duplicates_total", "Total de eventos descartados por ser duplicados"
)
ingestion_errors_total = Counter(
    "ingestion_errors_total", "Total de ciclos de ingesta que fallaron"
)
ingestion_cycle_duration_seconds = Histogram(
    "ingestion_cycle_duration_seconds", "Duracion de cada ciclo de ingesta"
)
