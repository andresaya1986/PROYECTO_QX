# Prueba Técnica: Procesamiento de Eventos en Tiempo Real
[cite_start]**Tecnologías:** MongoDB, Airflow, FastAPI y Docker [cite: 2]  
[cite_start]**Empresa:** Quipux [cite: 3]  
[cite_start]**Fecha:** 24 de junio de 2026 [cite: 4]  

---

## 1. Objetivo
[cite_start]Diseñar e implementar una plataforma capaz de consumir eventos desde una API pública, procesarlos en tiempo real (o near real-time), almacenarlos en MongoDB y generar reportes periódicos utilizando Airflow, FastAPI y Pydantic[cite: 6]. 

[cite_start]La solución debe seguir principios de diseño desacoplado, buenas prácticas de desarrollo y ejecutarse completamente mediante Docker Compose[cite: 7].

---

## 2. Contexto
[cite_start]El sistema debe monitorear eventos sísmicos publicados por el servicio **USGS Earthquake Program**[cite: 9].

* [cite_start]**API pública:** `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson` [cite: 11]
* [cite_start]**Descripción:** La API devuelve los terremotos detectados durante la última hora[cite: 12].

### Ejemplo simplificado de respuesta (JSON):
```json
{
  "features": [
    {
      "id": "us7000xxxx",
      "properties": {
        "mag": 4.2,
        "place": "20 km NW of California",
        "time": 1718610000000
      },
      "geometry": {
        "coordinates": [-120.12, 35.44, 10.5]
      }
    }
  ]
}