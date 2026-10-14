# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]

### Agregado
- Estructura inicial del repositorio y documentación base.
- Informes de investigación en `docs/investigacion/`: contexto del problema, fuentes de datos, dos informes de parámetros del Malbec y `verificacion-fuentes.md`, con los datos confirmados en las fuentes originales (SMN, INV, WSU, FAUBA, FDF, Morábito, Zapata 2017).
- ADR-003: decisiones iniciales de modelado (alertas con referencias, contenido de `lecturas.meta`, alerta de riego por humedad de suelo).
- ADR-004: temporada de Malbec, etapa fenológica BBCH estimada por grados-día y corregida con observaciones, índice de riesgo de helada, selector de fecha de referencia.
- ADR-005: temperatura estimada en el brote, umbrales de helada de vid por etapa, índice de riesgo con agravantes, riego y suelo por finca.
- Consultas Q9 (etapa por grados-día) y Q10 (índice de riesgo), y requisitos RF-16 a RF-20.
- `install.sh` y `requirements.txt` para crear el entorno de Python (`pymongo`, `streamlit`, `plotly`, versiones fijas).
- Spike de series temporales en MongoDB 9.0.2: scripts en `scripts/spike-adr001/` y conclusiones en `docs/spikes/`.
- Secciones "Cómo se probó" y "Conclusión" en la plantilla de spike.

### Cambiado
- Alcance: de 30 días sin variedad definida a una temporada de Malbec (1/9/2026 a 31/3/2027, unas 732.700 lecturas).
- Umbrales de helada: valores de vid por etapa BBCH en lugar de los de frutales (IDR + DACC).
- `lecturas` como serie temporal, confirmada como decisión firme (ADR-001).
- `eventos_climaticos` como colección común, porque el índice `2dsphere` de las series temporales solo acepta puntos.
- Q3 (nodos más cercanos) se resuelve con `$geoNear` sobre la colección `nodos`.
- `escenario_id` va dentro de `lecturas.meta`, para que "Reiniciar demo" pueda borrar las lecturas de la simulación en vivo.
- `CLAUDE.md` actualizado con las decisiones de las ADR y del spike.

### Corregido
- Mínimas récord de septiembre del SMN (San Rafael −4,5 °C y San Martín −2,8 °C) y altura de la estación San Martín (653 m), que venían mal de una fuente secundaria.
- Fin de línea LF en los scripts `.sh` (`.gitattributes`), para que funcionen al clonar en Windows.
