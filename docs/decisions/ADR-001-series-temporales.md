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
- Hay que verificar en la versión instalada de MongoDB las limitaciones de actualización y borrado (afecta a RF-15, "Reiniciar demo") y la combinación con índices geoespaciales.
- `performance.md` documenta el rendimiento de las consultas sobre la serie temporal.
