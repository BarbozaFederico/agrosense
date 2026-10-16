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
- Modelo de datos v1.0 (`docs/modelo-datos.md`): campos, tipos, relaciones, índices propuestos y ejemplos de las 10 colecciones, con la colección de configuración `configuracion`. ADR-006 con las decisiones de detalle (IDs legibles, etapas embebidas, validación estricta, entre otras).
- ADR-007: `lecturas` (serie temporal) no admite validador en MongoDB 9.0.2; se protege con validación en el simulador y con una consulta de auditoría.
- ADR-008: los esquemas, la creación de colecciones, la validación previa y la auditoría se escriben en Python (`pymongo`).
- Paquete `db`: esquemas `$jsonSchema` de las 10 colecciones (`db/schemas/`), conexión configurable con `AGROSENSE_URI` y `AGROSENSE_BD`, creación de colecciones repetible sin perder datos, validación de lecturas sin guardar (`$documents` + `$jsonSchema`), auditoría de lecturas y prueba de 62 casos. Documentado en `docs/esquemas-validacion.md`.
- Spike de esquemas de validación (4 pruebas): esquema cerrado, validador en series temporales, auditoría con `$nor` y validación desde Python.
- ADR-009: límite de temperatura "sospechosa" por departamento (`configuracion.sospechoso_minimo_c`: San Rafael −4,5 °C y San Martín −2,8 °C, récord de septiembre del SMN; Tupungato `null`, a validar) y noche extrema declarada en `configuracion.noche_extrema` (San Rafael, primera semana de octubre, piso −6,3 °C supuesto). El límite es techo de generación del simulador y aviso de auditoría; no rechaza ni excluye lecturas.
- Auditoría de lecturas con tres conteos (mal formadas, sospechosas esperadas e inesperadas) que aprueba con dos ceros y termina con código 1 si falla; `configuracion.verificar_coherencia()` con las reglas que el esquema no puede expresar; `db/departamentos.py`. La prueba pasó a 62 casos.

### Cambiado
- Alcance: de 30 días sin variedad definida a una temporada de Malbec (1/9/2026 a 31/3/2027, unas 732.700 lecturas).
- Umbrales de helada: valores de vid por etapa BBCH en lugar de los de frutales (IDR + DACC).
- `lecturas` como serie temporal, confirmada como decisión firme (ADR-001).
- `eventos_climaticos` como colección común, porque el índice `2dsphere` de las series temporales solo acepta puntos.
- Q3 (nodos más cercanos) se resuelve con `$geoNear` sobre la colección `nodos`.
- `escenario_id` va dentro de `lecturas.meta`, para que "Reiniciar demo" pueda borrar las lecturas de la simulación en vivo.
- `CLAUDE.md` actualizado con las decisiones de las ADR y del spike.
- Los scripts de los spikes pasaron de `mongosh` a Python, con resultados idénticos.
- `eventos_climaticos.tipo` solo admite `"helada"`: el granizo queda fuera del modelo porque ningún sensor del MVP lo mide (ADR-006, decisión 12).

### Corregido
- Ejemplo de `variedades` en `modelo-datos.md`: la etapa "Floración y cuaje" lleva 260 grados-día desde la brotación (Zapata 2017), no 230.
- Mínimas récord de septiembre del SMN (San Rafael −4,5 °C y San Martín −2,8 °C) y altura de la estación San Martín (653 m), que venían mal de una fuente secundaria.
- Fin de línea LF en los scripts `.sh` (`.gitattributes`), para que funcionen al clonar en Windows.
