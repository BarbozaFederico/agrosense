# ADR-001: Series temporales para las lecturas

**Estado:** Aceptado por el equipo (8/10/2026). Falta informarlo al docente; si lo rechaza, se aplica la regla de decisión por defecto.

## Contexto

Las lecturas de sensores son documentos muy numerosos, con la misma forma y ordenados en el tiempo. MongoDB ofrece colecciones de series temporales pensadas para ese caso. No sabemos si el docente considera ese tema dentro del alcance de la materia, y la combinación con índices geoespaciales debe probarse en la versión instalada.

## Decisión

Usar una colección de series temporales para `lecturas` (`timeField: ts`, `metaField: meta`).

## Regla de decisión por defecto

Si antes de cerrar el Sprint A el docente no lo confirma, o si la prueba con la versión instalada falla, `lecturas` se implementa como **colección común con índice compuesto** (`meta.parcela_id` y `ts`).

## Alternativas

| Alternativa | Ventaja | Desventaja |
|---|---|---|
| Serie temporal | Almacenamiento y consultas optimizados para datos temporales | Posibles limitaciones con índices y operaciones; puede salir del alcance de la materia |
| Colección común con índice compuesto | Simple y dentro del alcance seguro | Menos eficiente con grandes volúmenes |

## Consecuencias

- `lecturas` se crea como serie temporal (`timeField: ts`, `metaField: meta`, con `meta` = `nodo_id`, `parcela_id`, `finca_id`, según ADR-003).
- Hay que verificar en la versión instalada de MongoDB las limitaciones de actualización y borrado en series temporales (afecta a RF-15, "Reiniciar demo") y la combinación con índices geoespaciales.
- `performance.md` documenta el rendimiento de las consultas sobre la serie temporal.
