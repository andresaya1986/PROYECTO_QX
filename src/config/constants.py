EARTHQUAKES_COLLECTION = "earthquakes"
METRICS_COLLECTION = "metrics"
HOURLY_REPORTS_COLLECTION = "hourly_reports"

# Rangos de magnitud Richter usados para la distribución de métricas.
# Definidos según la escala estándar del USGS (micro/minor/light/moderate/strong+).
MAGNITUDE_RANGES = [
    ("micro", float("-inf"), 2.0),
    ("minor", 2.0, 4.0),
    ("light", 4.0, 5.0),
    ("moderate", 5.0, 6.0),
    ("strong", 6.0, float("inf")),
]


def classify_magnitude(magnitude: float) -> str:
    for label, lower, upper in MAGNITUDE_RANGES:
        if lower <= magnitude < upper:
            return label
    return "unknown"
