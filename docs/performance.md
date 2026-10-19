# Rendimiento

**Estado:** esqueleto. Las consultas Q1 a Q10 ya existen ([`consultas.md`](consultas.md)) y los únicos índices creados son los tres `2dsphere` que Q3 y Q4 necesitan (`python -m db.indexes.crear_indices`, ADR-014). Falta medir.

Mediciones con `explain("executionStats")` antes y después de aplicar índices, para al menos 3 consultas (RNF-01).

Candidatas, sin ningún índice de rendimiento creado todavía (se mide el "antes" con la base como está):

| Consulta | Índice a probar | Por qué |
|---|---|---|
| Q7 (`riegos`) | `{ parcela_id: 1, inicio: 1 }` | Filtra por parcela y rango de fechas |
| Q8 (`alertas`) | `{ tipo: 1, inicio: 1 }` | Filtra por tipo de alerta |
| Q9 (`observaciones_fenologicas`) | `{ parcela_id: 1, fecha: -1 }` | Última observación de cada parcela |
| Q1, Q5, Q6, Q9, Q10 (`lecturas`) | El índice `{ meta: 1, ts: 1 }` ya lo crea MongoDB | Medir cuánto ayuda y si hace falta otro |

| Consulta | Índice | Documentos examinados antes | Documentos examinados después | Tiempo antes | Tiempo después |
|---|---|---|---|---|---|
| *A completar* | | | | | |

## Cómo se midió

*A completar:* cantidad de documentos, versión de MongoDB, equipo usado.
