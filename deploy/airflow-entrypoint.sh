#!/usr/bin/env bash
set -e

airflow db migrate

airflow users create \
  --username "${AIRFLOW_ADMIN_USER:-admin}" \
  --password "${AIRFLOW_ADMIN_PASSWORD:-change-me}" \
  --firstname Quipux \
  --lastname Admin \
  --role Admin \
  --email admin@example.com || true

airflow dags unpause hourly_report_dag || true

airflow scheduler &
exec airflow webserver
