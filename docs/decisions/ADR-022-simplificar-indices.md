# ADR-022: Simplificar los índices, de 7 a 4

**Estado:** Aceptado (4/11/2026). Reemplaza la decisión 2 de [ADR-015](ADR-015-indices-de-rendimiento.md) (qué índices se crean) y la decisión 11 de [ADR-014](ADR-014-consultas-en-python.md) (el `2dsphere` de `eventos_climaticos`). Mediciones en [`performance.md`](../performance.md). Requisito RNF-01.

## Contexto

ADR-015 dejó 7 índices: 3 `2dsphere` y 4 de rendimiento. Al preparar la explicación de cada uno apareció un problema: varios eran difíciles de justificar. Se revisó cuáles aportan algo de verdad, midiendo y no por intuición, y se encontró lo siguiente:

- Solo **uno** de los `2dsphere` es obligatorio: sin el de `nodos`, Q3 (`$geoNear`) falla. Q4 devuelve exactamente lo mismo sin el de `parcelas`.
- El `2dsphere` de `eventos_climaticos` **no lo usa ninguna consulta**: Q4 lee el evento por `_id` y la búsqueda geoespacial es sobre `parcelas`.
- Los índices de `alertas` y de `observaciones_fenologicas` ahorran pocos documentos y no cambian el tiempo.
- El de `riegos` es el más claro de los de rendimiento: pasa de leer toda la colección a leer solo los riegos de la parcela.

## Decisiones

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 1 | Criterio | Un índice se mantiene si la consulta **falla** sin él, o si baja los documentos examinados de forma clara **y** se explica en una línea | Dejar todos los que mejoran algo: la mejora de 20 a 50 documentos no justifica explicar el índice |
| 2 | Se mantienen 4 | `nodos` `2dsphere` (Q3 falla sin él), `parcelas` `2dsphere` (Q4), `lecturas {meta.nodo_id, ts}` (Q5: 5.053 → 433, −91 %) y `riegos {parcela_id, inicio}` (Q7: 563 → 33, −94 %) | - |
| 3 | `parcelas` `2dsphere` | Se deja aunque **no es obligatorio** (Q4 funciona igual con un COLLSCAN sobre 6 parcelas): es el par natural de Q3 y mantiene la explicación de "geoespacial" en un solo lugar | Borrarlo (queda lo mínimo, pero Q4 deja de usar un índice geoespacial) |
| 4 | Se descarta `eventos_climaticos` `2dsphere` | Ninguna consulta lo usa. Q4: 5 documentos examinados con y sin él | Dejarlo "por simetría" |
| 5 | Se descarta `alertas {tipo, inicio}` | Q8: 57 → 32 documentos y 2,5 → 2,2 ms (ruido). La colección tiene 35 documentos y `tipo` solo 2 valores (selectividad baja). Las consultas de la pantalla Alertas del dashboard leen la colección entera igual | Dejarlo porque el Resumen lo usa (8 documentos en lugar de 35) |
| 6 | Se descarta `observaciones_fenologicas {parcela_id, fecha}` | Q9: 1.092 → 846 documentos (−22 %) y 31,2 → 31,1 ms. Es el más difícil de explicar, porque trabaja adentro de un `$lookup`. El tiempo de Q9, Q2 y Q10 lo domina la lectura de `lecturas` | Dejarlo por ser el que más documentos ahorra de los descartados |
| 7 | Limpieza | `crear_indices.py` crea los 4 y **borra** los 3 descartados si la base los tiene (por ejemplo una hecha antes de este ADR). La lista `INDICES_DESCARTADOS` los nombra | Borrarlos a mano (no es reproducible) |
| 8 | Evidencia | Las mediciones se **conservan**: `medir_indices.py` crea cada candidato descartado, mide las consultas que podría mejorar y lo borra. La tabla va en `performance.md` | Borrar las mediciones (se pierde el porqué de cada ausencia) |

## Consecuencias

- La base pasa de 7 a 4 índices de este proyecto (más el automático `meta_1_ts_1` de la serie temporal). Ocupan 176 KB en lugar de 236 KB.
- **Q2, Q8, Q9 y Q10 quedan sin índice propio.** Q9 vuelve a examinar 1.092 documentos en lugar de 846; no cambia el tiempo (31,2 ms sin el índice de observaciones y 31,1 ms con él, dentro del ruido). Si el volumen de observaciones, alertas o riegos crece mucho, se reevalúa con `medir_indices.py`.
- RNF-01 sigue cumplido: tienen medición antes y después Q3 (falla → funciona), Q5 (−91 %) y Q7 (−94 %), además de Q4.
- `probar_indices.py` pasa a 20 casos y agrega dos que respaldan esta decisión: Q3 **falla** sin el índice de `nodos`, y Q4 devuelve lo mismo con y sin el de `parcelas`. Comprueba además que los descartados no se crean y que se borran de una base que los tenga.
- El resumen de la defensa baja de "7 índices" a "4 índices, cada uno con una razón de una línea, y 3 que medimos y descartamos".
- En el dashboard, la consulta de "último riego" lee la colección entera y no usa el índice de `riegos`; solo lo usan Q7 y la pantalla de detalle. No cambia nada porque son 563 documentos.
