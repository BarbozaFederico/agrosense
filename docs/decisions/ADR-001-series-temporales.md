# ADR-001: Series temporales para las lecturas

**Estado:** Aceptado (8/10/2026).

## Contexto

Las lecturas de sensores son documentos muy numerosos (unas 732.700 en la temporada simulada), con la misma forma y ordenados en el tiempo. MongoDB ofrece colecciones de series temporales pensadas exactamente para ese caso.

## Decisión

Usar una colección de series temporales para `lecturas` (`timeField: ts`, `metaField: meta`). Es la decisión lógica para el tipo de dato: el motor está optimizado para guardar y consultar mediciones ordenadas en el tiempo.

## Alternativas

| Alternativa | Ventaja | Desventaja |
|---|---|---|
| **Serie temporal (elegida)** | Almacenamiento y consultas optimizados para datos temporales | Limitaciones en actualizaciones, borrados y algunos índices |
| Colección común con índice compuesto | Simple, sin limitaciones especiales | Menos eficiente con grandes volúmenes |

## Consecuencias

- `lecturas` se crea como serie temporal, con `meta` = `nodo_id`, `parcela_id` y `finca_id` (ADR-003).
- **Verificado en MongoDB 9.0.2** ([spike del 14/10/2026](../spikes/spike-adr001-series-temporales.md)):
  - Borrar se puede con cualquier filtro: "Reiniciar demo" (RF-15) borra por `meta.escenario_id`, así que `escenario_id` va dentro de `meta`.
  - Actualizar solo se puede con `updateMany` y sobre campos de `meta`: las lecturas no se corrigen, se borran y se vuelven a insertar.
  - El índice `2dsphere` en series temporales solo acepta puntos: `eventos_climaticos` (polígonos) va como colección común, y Q3 usa `$geoNear` sobre la colección `nodos`.
- `performance.md` documenta el rendimiento de las consultas sobre la serie temporal.
