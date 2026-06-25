# Plataforma de Procesamiento de Eventos Sísmicos en Tiempo Real

Prueba técnica para Quipux: ingesta, procesamiento near-real-time, persistencia en MongoDB,
API REST con FastAPI y reportes horarios con Airflow, sobre eventos sísmicos del
[USGS Earthquake Program](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson).

Ver el detalle completo de requerimientos en [`contexto_prueba.md`](contexto_prueba.md).

## Arquitectura

Ver [`docs/architecture.md`](docs/architecture.md) para el diagrama y la justificación de decisiones
de diseño (modelado de datos, índices, caché, observabilidad).

```
src/
├── config/       # settings (env vars), logging estructurado, constantes
├── models/       # esquemas Pydantic (dominio + GeoJSON de USGS)
├── database/     # cliente Mongo, índices, repositorios
├── clients/      # cliente HTTP del feed de USGS
├── services/     # ingestion / processing / metrics / reporting
├── ingestion/     # worker que corre el loop de ingesta cada 3 min
├── api/          # FastAPI: rutas, dependencias, instrumentación Prometheus
└── utils/        # caché TTL, métricas custom
airflow/dags/      # DAG horario de reportes consolidados
monitoring/        # configuración de Prometheus y provisioning de Grafana
deploy/            # Dockerfiles
```

## Servicios (docker-compose)

| Servicio          | Puerto | Descripción                                                |
|-------------------|--------|--------------------------------------------------------------|
| `mongodb`         | 27017  | Persistencia (colecciones `earthquakes`, `metrics`, `hourly_reports`) |
| `ingestion`       | 9100   | Worker que consulta USGS cada 3 min, dedupe + métricas. Expone métricas Prometheus |
| `api`             | 8000   | API REST (FastAPI). Swagger en `/docs` |
| `airflow-postgres`| -      | Metadata DB de Airflow |
| `airflow`         | 8080   | Scheduler + Webserver (LocalExecutor). DAG `hourly_report_dag` |
| `prometheus`      | 9090   | Scrapea métricas de `api` y `ingestion` |
| `grafana`         | 3000   | Dashboard "Quipux - Earthquakes Overview" |

## Cómo ejecutar

1. Copiar el archivo de variables de entorno y ajustar si es necesario (no se usan credenciales hardcodeadas en el código):

   ```bash
   cp .env.example .env
   ```

2. Levantar todo el stack:

   ```bash
   docker compose up -d --build
   ```

   La primera vez tarda varios minutos (build de imágenes + migración de Airflow). Se puede seguir el progreso con:

   ```bash
   docker compose logs -f
   ```

3. Servicios disponibles:
   - API: http://localhost:8000/docs
   - Airflow UI: http://localhost:8080 (usuario/clave: `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` del `.env`)
   - Grafana: http://localhost:3000 (usuario/clave: `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD` del `.env`)
   - Prometheus: http://localhost:9090

4. Para detener todo:

   ```bash
   docker compose down
   ```

   Agregar `-v` si además se quieren borrar los volúmenes (datos de Mongo, Postgres de Airflow, Grafana).

## Endpoints principales

- `GET /earthquakes` — filtros (`min_magnitude`, `max_magnitude`, `location`, `start_time`, `end_time`),
  paginación (`page`, `page_size`), orden (`sort_by`, `order`). Validación con Pydantic.
- `GET /metrics` — métricas agregadas por ventana horaria (`window=YYYY-MM-DDTHH`, o la más reciente si no se especifica).
- `GET /reports` — reportes horarios generados por el DAG de Airflow (`start_date`, `end_date`, paginación).
- `GET /health` — liveness/readiness.

Colección de Postman lista para importar: [`postman/quipux_earthquakes.postman_collection.json`](postman/quipux_earthquakes.postman_collection.json).

## Airflow

El DAG `hourly_report_dag` corre cada hora (`0 * * * *`) y tiene 3 tasks (visibles por separado en la UI
para facilitar el monitoreo): `extract_events` → `generate_report` → `persist_report`. Reutiliza
`src/services/reporting_service.py` (el mismo código que podría usar la API), montado como volumen
dentro del contenedor de Airflow.

Para disparar el DAG manualmente sin esperar la hora en punto:

```bash
docker exec proyecto_qx-airflow-1 airflow dags trigger hourly_report_dag
```

## Decisiones de diseño (resumen)

- **Dedup de eventos**: índice único en `earthquakes.event_id` + upsert (`$setOnInsert`). Mongo
  garantiza la unicidad sin lógica de "verificar si existe" antes de insertar.
- **Métricas en tiempo real**: `metrics_service` hace un upsert atómico (`$inc`/`$max`) por ventana
  horaria en cada evento nuevo ingerido, evitando recalcular agregados sobre toda la colección.
  `avg_magnitude` se deriva de `sum_magnitude / earthquake_count` al leer.
- **Rangos de magnitud** (definidos por el candidato, en `src/config/constants.py`): micro (<2),
  minor (2–3.9), light (4–4.9), moderate (5–5.9), strong (≥6) — escala Richter estándar del USGS.
- **Capas/SOLID**: `usgs_client` → `ingestion_service` → `processing_service` → `metrics_service`,
  con acceso a Mongo encapsulado en repositorios inyectados (inversión de dependencias).
- **Caché**: `cachetools.TTLCache` en memoria sobre las lecturas agregadas de `/metrics` y `/reports`
  (`CACHE_TTL_SECONDS`, default 30s). No se usa Redis para no añadir un servicio más en un take-home;
  sería la alternativa natural si se necesitara compartir caché entre réplicas de la API.
- **Logging estructurado**: JSON vía `logging` estándar (sin dependencias extra), igual en ingesta y API.
- **Observabilidad**: métricas custom de negocio (`earthquakes_ingested_total`, `earthquakes_duplicates_total`,
  `ingestion_errors_total`, `ingestion_cycle_duration_seconds`) más métricas HTTP automáticas de la API
  vía `prometheus-fastapi-instrumentator`, expuestas en `/prometheus-metrics` (se evitó el nombre `/metrics`
  porque ese path ya es el endpoint de negocio pedido por el spec).

## Alcance no implementado (a propósito)

Por el spec: autenticación, autorización, frontend, CI/CD y despliegue en cloud no son necesarios.
Tampoco se implementaron las bonificaciones de Nivel 3 (Kafka/RabbitMQ/WebSockets) ni Nivel 4
(arquitectura analítica/ML) — el diseño actual (servicios desacoplados, repositorios) facilita
agregarlas después sin reescribir la lógica de negocio.
