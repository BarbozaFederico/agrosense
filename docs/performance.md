# Rendimiento

**Estado:** medido (4/11/2026; la primera medición fue el 20/10/2026). Decisiones en [ADR-015](decisions/ADR-015-indices-de-rendimiento.md) (cómo se mide) y [ADR-022](decisions/ADR-022-simplificar-indices.md) (qué índices quedan). Requisito RNF-01: mediciones antes y después de aplicar índices para al menos 3 consultas.

## Cómo leer las tablas

Un **índice** es una estructura auxiliar que permite a MongoDB encontrar documentos sin leer toda la colección. Sin índice, para encontrar los riegos de una parcela revisa todos (**COLLSCAN**); con índice va directo a los que corresponden (**IXSCAN**). Se mide con tres cifras:

| Cifra | Qué es | Por qué importa |
|---|---|---|
| **Documentos examinados** | Cuántos documentos tuvo que leer MongoDB para armar la respuesta | Es la cifra principal: no depende de la velocidad de la computadora. En una serie temporal (`lecturas`) cuenta "buckets" (grupos de lecturas), no lecturas sueltas |
| **Claves de índice** | Cuántas entradas de índice recorrió | Si los documentos son muchos y las claves son 0, no usó ningún índice |
| **Tiempo (ms)** | Mediana de 10 corridas después de una de calentamiento | Es secundaria: con estos tamaños todo tarda menos de 50 ms y la diferencia es del orden del ruido |

`explain("executionStats")` no muestra lo que ocurre adentro de un `$lookup`, que es justo donde está el trabajo de Q5 y Q9. Por eso las cifras salen del **perfilador** de MongoDB (`db.setProfilingLevel`), que suma todo lo que leyó cada comando. Los planes de una sola colección (Q7) se confirman además con `explain()` en la prueba automática.

## Los 4 índices que se mantienen

Cada uno tiene una razón de una línea:

| Colección | Índice | Para | Por qué |
|---|---|---|---|
| `nodos` | `ubicacion_2dsphere` | Q3 | **Obligatorio:** sin él, `$geoNear` falla ("unable to find index") |
| `parcelas` | `geometria_2dsphere` | Q4 | Opcional: Q4 anda igual sin él. Se deja como par geoespacial de Q3 (ADR-022, decisión 3) |
| `lecturas` | `{meta.nodo_id: 1, ts: -1}` | Q5 | Baja de 5.053 a 433 los documentos examinados (−91 %) en la colección grande |
| `riegos` | `{parcela_id: 1, inicio: 1}` | Q7 | Pasa de leer los 563 riegos a leer solo los 33 de la parcela (−94 %): Q7 pide una parcela y un rango de fechas, que es el orden del índice |

## Resultados: antes y después de crear los 4 índices

Medido el 4/11/2026 en la base `agrosense_tests` (mismos datos que `agrosense`): MongoDB 9.0.2, 727.980 lecturas, Windows 11 con 16 núcleos lógicos, Python 3.13.

| Consulta | Qué responde | Índice que le sirve | Documentos examinados | Claves de índice | Tiempo (ms) | Plan |
|---|---|---|---|---|---|---|
| Q1 | horas bajo cero de una noche | - | 30 | 6 | 9,8 → 9,9 | CLUSTERED_IXSCAN |
| Q2 | parcelas bajo el umbral | - | 1.121 | 425 | 33,5 → 34,3 | CLUSTERED_IXSCAN + EXPRESS_IXSCAN |
| Q3 | nodos más cercanos | nodos 2dsphere | falla → 12 | falla → 43 | falla → 3,1 | falla → GEO_NEAR_2DSPHERE |
| Q4 | parcelas dentro de un evento | parcelas 2dsphere (opcional) | 9 → 5 | 2 → 8 | 1,2 → 1,4 | COLLSCAN → COLLSCAN + IXSCAN |
| **Q5** | **nodos sin reportar** | **lecturas** | **5.053 → 433** | 1 → 432 | 9,5 → 7,8 | COLLSCAN + EXPRESS_IXSCAN |
| Q6 | humedad de suelo por hora | - | 24 | 0 | 2,1 → 2,0 | CLUSTERED_IXSCAN |
| **Q7** | **litros por parcela y semana** | **riegos** | **563 → 33** | 0 → 33 | 1,8 → 1,5 | **COLLSCAN → IXSCAN** |
| Q8 | heladas por departamento | - | 57 | 22 | 2,0 → 2,5 | COLLSCAN |
| Q9 | etapa por grados-día | - | 1.092 | 420 | 30,3 → 31,2 | CLUSTERED_IXSCAN |
| Q10 | índice de riesgo de helada | - | 1.127 | 422 | 47,8 → 47,8 | CLUSTERED_IXSCAN + COLLSCAN + EXPRESS_IXSCAN |

En negrita, las dos que mejoran con un índice de rendimiento propio. Cómo interpretar cada fila:

- **Q5 (la mejora más grande, 91 % menos):** su `$lookup` a `lecturas` busca la última lectura de cada nodo por `meta.nodo_id`. El índice automático de la serie temporal está sobre `meta` completo, así que no le sirve (1 clave examinada). Con `{meta.nodo_id: 1, ts: -1}` pasa de recorrer todos los grupos de cada nodo a leer 433.
- **Q7:** leía la colección entera (COLLSCAN, 563 documentos) para armar 31 filas de resultado. Con el índice lee solo los 33 riegos de la parcela.
- **Q3:** sin el índice `2dsphere`, `$geoNear` falla. Es un índice necesario, no una optimización. La prueba automática lo comprueba (el caso "Q3 FALLA sin el índice").
- **Q4:** pasa de COLLSCAN a IXSCAN, pero con 6 parcelas no hay diferencia real (y en tiempo es 0,2 ms más lenta, que es ruido y el costo de consultar el índice). Devuelve exactamente lo mismo con y sin el índice, y la prueba automática también lo comprueba.
- **Q1 y Q6:** ya se resolvían bien. `lecturas` es una serie temporal y MongoDB la lee por tiempo (CLUSTERED_IXSCAN), así que 24 a 30 grupos alcanzan para una noche o un día. No hace falta ningún índice.
- **Q2, Q8, Q9 y Q10:** quedan sin índice propio. Se midió qué pasaría con uno (sección siguiente) y no vale su costo.

**Sobre los tiempos:** las diferencias son de 1 o 2 ms y a veces el "después" es más lento (Q4, Q8). Es ruido de medición. Con 563 riegos o 35 alertas la colección cabe en memoria y leerla toda es casi gratis. El índice importa cuando la colección crece (extrapolación lineal, no medida: con 100 veces más riegos, Q7 leería unos 56.300 documentos sin índice contra unos 3.300 con él); lo que se puede afirmar con estos datos es la reducción de documentos examinados, no la del tiempo.

## Candidatos descartados: qué aportarían

Se crearon tres índices más en la primera versión (ADR-015). Al revisarlos, no justificaban su costo ni su explicación (ADR-022). `medir_indices.py` los sigue midiendo: crea cada uno, mide las consultas que podría mejorar, y lo borra. La comparación es "con los 4 elegidos" contra "con los 4 elegidos más el candidato".

| Candidato | Consulta | Documentos examinados sin / con | Tiempo (ms) sin / con | Tamaño |
|---|---|---|---|---|
| `eventos_climaticos` `area_2dsphere` | Q4 | 5 / 5 | 1,4 / 1,5 | 20,0 KB |
| `alertas` `tipo_1_inicio_1` | Q8 | 57 / 32 | 2,5 / 2,2 | 20,0 KB |
| `observaciones_fenologicas` `parcela_id_1_fecha_-1` | Q9 | 1.092 / 846 | 31,2 / 31,1 | 20,0 KB |
| `observaciones_fenologicas` `parcela_id_1_fecha_-1` | Q2 | 1.121 / 875 | 34,3 / 33,9 | 20,0 KB |
| `observaciones_fenologicas` `parcela_id_1_fecha_-1` | Q10 | 1.127 / 881 | 47,8 / 46,8 | 20,0 KB |

Por qué se descartaron:

- **`eventos_climaticos.area`:** ninguna consulta lo usa. Q4 lee el evento por `_id` y la búsqueda geoespacial es sobre `parcelas`. Examina 5 documentos con y sin él.
- **`alertas {tipo, inicio}`:** la colección tiene 35 documentos y `tipo` solo 2 valores, así que casi no filtra. Las consultas de la pantalla Alertas del dashboard leen la colección entera igual. La diferencia de tiempo (0,3 ms) es ruido.
- **`observaciones_fenologicas {parcela_id, fecha}`:** ahorra ~245 documentos de ~1.100 (−22 %) pero el tiempo no cambia: lo domina la lectura de `lecturas`. Además es el más difícil de explicar, porque trabaja adentro de un `$lookup`.

## Experimento: ¿hace falta el índice automático de `lecturas`?

MongoDB crea solo `meta_1_ts_1` en una serie temporal. Se lo borró en la base de pruebas, se midieron las consultas que leen `lecturas` y se lo volvió a crear (en `agrosense` nunca se borra):

| Consulta | Documentos examinados con / sin `meta_1_ts_1` | Tiempo (ms) con / sin |
|---|---|---|
| Q1 | 30 / 30 | 9,9 / 9,8 |
| Q5 | 433 / 433 | 7,8 / 8,1 |
| Q6 | 24 / 24 | 2,0 / 1,9 |
| Q9 | 1.092 / 1.092 | 31,2 / 30,4 |

**Conclusión:** ninguna consulta de este proyecto usa `meta_1_ts_1`: el acceso por tiempo propio de la serie temporal ya alcanza. Igual se lo deja, porque lo crea MongoDB, ocupa poco (104 KB) y borrarlo no ahorra nada que valga la pena; es una respuesta a "¿por qué no indexaron `lecturas`?": ya está indexada y solo faltaba el índice de Q5.

## Costo: lo que ocupa cada índice

Un índice no es gratis: ocupa espacio y hace más lenta cada escritura (hay que actualizarlo).

| Colección | Índice | Tamaño | Para |
|---|---|---|---|
| nodos | `ubicacion_2dsphere` | 20,0 KB | Q3 |
| parcelas | `geometria_2dsphere` | 20,0 KB | Q4 |
| lecturas | `meta.nodo_id_1_ts_-1` | 112,0 KB | Q5 |
| riegos | `parcela_id_1_inicio_1` | 24,0 KB | Q7 |
| lecturas | `meta_1_ts_1` (automático) | 104,0 KB | referencia |

Los 4 índices suman 176 KB (con los 3 descartados eran 236 KB). El de `lecturas` es el único que toca la colección grande y cada lectura nueva tiene que actualizarlo (no se midió cuánto cuesta); por eso `crear_indices.py` se corre después de `simulator.generar`, que carga toda la temporada de una vez.

## Qué índices NO se crean y por qué

| Candidato | Motivo |
|---|---|
| `eventos_climaticos` `2dsphere`, `alertas {tipo, inicio}` y `observaciones_fenologicas {parcela_id, fecha}` | Medidos y descartados (sección anterior, ADR-022) |
| `alertas {estado, tipo}` (propuesto en `modelo-datos.md`) | Ninguna consulta filtra por `estado`; Q8 filtra por `tipo` |
| `alertas {parcela_id, inicio}` (propuesto en `modelo-datos.md`) | Q8 no filtra por parcela, y la pantalla Alertas del dashboard lee 35 documentos |
| Otro índice en `lecturas` (por parcela o por finca) | Q1, Q6, Q9 y Q10 ya usan CLUSTERED_IXSCAN con 24 a 1.100 grupos examinados |
| Índices en `fincas`, `parcelas` (por `finca_id`) o `variedades` | Colecciones de 1 a 6 documentos |

## Cómo reproducirlo

```bash
python -m db.indexes.medir_indices            # imprime las tablas de arriba (usa agrosense_tests, ~10 s)
python -m db.indexes.probar_indices           # 20 casos: planes, mejoras y que ningún resultado cambia
python -m db.indexes.crear_indices            # crea los 4 índices (y borra los descartados) en la base de AGROSENSE_BD
```

`medir_indices` borra y crea índices, por eso trabaja siempre sobre `agrosense_tests`. Los números de tiempo dependen de la computadora; los de documentos examinados deberían repetirse.
