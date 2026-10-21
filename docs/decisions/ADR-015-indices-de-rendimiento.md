# ADR-015: Índices de rendimiento y cómo se miden

**Estado:** Aceptado (20/10/2026). Completa [ADR-014](ADR-014-consultas-en-python.md) (índices geoespaciales). Resultados en [`performance.md`](../performance.md). Requisito RNF-01.

## Contexto

`modelo-datos.md` (sección 8) proponía una lista de índices sin medirlos. Al correr `explain` sobre las consultas Q1 a Q10 aparecieron tres cosas: `riegos` y `alertas` se leían enteras (COLLSCAN), `lecturas` ya se leía por tiempo (CLUSTERED_IXSCAN, 3 a 47 ms) y Q5 examinaba 5.053 documentos porque su `$lookup` a `lecturas` no usaba el índice automático de la serie temporal.

## Decisiones

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 1 | Qué se mide | Las 10 consultas, antes y después. Índice nuevo solo donde la medición lo justifica; en las otras queda escrito por qué no hace falta | Medir solo 3 o 4 (no muestra qué pasó con las demás) |
| 2 | Índices de rendimiento | `lecturas {meta.nodo_id: 1, ts: -1}` (Q5), `riegos {parcela_id: 1, inicio: 1}` (Q7), `alertas {tipo: 1, inicio: 1}` (Q8) y `observaciones_fenologicas {parcela_id: 1, fecha: -1}` (Q9) | `alertas {estado, tipo}` de `modelo-datos.md`: ninguna consulta filtra por `estado`. Un índice para la pantalla de alertas del dashboard, que todavía no existe |
| 3 | Arreglo de Q5 | Índice nuevo sobre un campo de `meta`; MongoDB lo admite en una serie temporal | Reescribir la consulta para usar `meta_1_ts_1` (depende del orden exacto de los campos de `meta`, frágil) |
| 4 | Qué cifras | Plan, documentos examinados y claves (con el perfilador de MongoDB, que cuenta también el trabajo de los `$lookup`) y mediana de 10 corridas con una de calentamiento. La cifra principal son los documentos examinados | Solo `explain()` (no muestra el interior de un `$lookup`); solo el tiempo (todo tarda menos de 50 ms, la diferencia es ruido) |
| 5 | Dónde se mide | En `agrosense_tests` con los datos reales de la temporada. El script borra y crea índices ahí; en `agrosense` solo se crean | Medir en `agrosense` (una falla dejaría la base real a medio indexar); inventar datos para una prueba de escala |
| 6 | Índice automático de `lecturas` | **Se deja.** Se mide un experimento en la base de pruebas (se borra, se miden Q1, Q5, Q6 y Q9, se vuelve a crear) que muestra que ninguna consulta lo usa, y se documenta | Borrarlo en la base real (ahorra 104 KB y no aporta nada) |
| 7 | Costo | Se informa el tamaño de cada índice | No informarlo |

## Consecuencias

- `db/indexes/crear_indices.py` crea los 3 índices `2dsphere` y los 4 de rendimiento; se corre después de `simulator.generar`. `medir_indices.py` imprime las tablas de `performance.md`, y `probar_indices.py` (19 casos) comprueba que los índices existen, que MongoDB los usa, que bajan los documentos examinados y que **ninguna respuesta cambia** al agregarlos.
- El resultado honesto: la mejora está en los documentos examinados (Q5 −91 %, Q7 −94 %), no en el tiempo, porque las colecciones son chicas. Q4, Q8 y Q10 incluso tardan una fracción de ms más. La defensa es esa: el índice vale cuando la colección crece.
- `modelo-datos.md` (sección 8) se corrige: `alertas {tipo, inicio}` en lugar de `{parcela_id, inicio}` y `{estado, tipo}`, y `lecturas {meta.nodo_id, ts}`.
- Si el dashboard agrega una pantalla de "alertas activas", habrá que medir si hace falta un índice por `estado`.
- `perfilar()` y `crear_indices` usan la base indicada por `AGROSENSE_BD`; las mediciones y la prueba fijan `agrosense_tests` para no tocar la real.
