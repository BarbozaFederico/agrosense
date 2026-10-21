# Rendimiento

**Estado:** medido (20/10/2026). Decisiones en [ADR-015](decisions/ADR-015-indices-de-rendimiento.md). Requisito RNF-01: mediciones antes y después de aplicar índices para al menos 3 consultas.

## Cómo leer las tablas

Un **índice** es una estructura auxiliar que permite a MongoDB encontrar documentos sin leer toda la colección. Sin índice, para encontrar los riegos de una parcela revisa todos (**COLLSCAN**); con índice va directo a los que corresponden (**IXSCAN**). Se mide con tres cifras:

| Cifra | Qué es | Por qué importa |
|---|---|---|
| **Documentos examinados** | Cuántos documentos tuvo que leer MongoDB para armar la respuesta | Es la cifra principal: no depende de la velocidad de la computadora. En una serie temporal (`lecturas`) cuenta "buckets" (grupos de lecturas), no lecturas sueltas |
| **Claves de índice** | Cuántas entradas de índice recorrió | Si los documentos son muchos y las claves son 0, no usó ningún índice |
| **Tiempo (ms)** | Mediana de 10 corridas después de una de calentamiento | Es secundaria: con estos tamaños todo tarda menos de 50 ms y la diferencia es del orden del ruido |

`explain("executionStats")` no muestra lo que ocurre adentro de un `$lookup`, que es justo donde está el trabajo de Q5 y Q9. Por eso las cifras salen del **perfilador** de MongoDB (`db.setProfilingLevel`), que suma todo lo que leyó cada comando. Los planes de una sola colección (Q7, Q8) se confirman además con `explain()` en la prueba automática.

## Resultados: antes y después de crear los índices

Medido el 20/10/2026 en la base `agrosense_tests` (mismos datos que `agrosense`): MongoDB 9.0.2, 727.980 lecturas, Windows 11 con 16 núcleos lógicos, Python 3.13.

| Consulta | Qué responde | Índice que le sirve | Documentos examinados | Claves de índice | Tiempo (ms) | Plan |
|---|---|---|---|---|---|---|
| Q1 | horas bajo cero de una noche | - | 30 | 6 | 9,8 → 9,6 | CLUSTERED_IXSCAN |
| Q2 | parcelas bajo el umbral | observaciones (por Q9) | 1.121 → 875 | 425 → 431 | 33,7 → 33,9 | CLUSTERED_IXSCAN + EXPRESS_IXSCAN |
| Q3 | nodos más cercanos | nodos 2dsphere | falla → 12 | falla → 43 | falla → 2,3 | falla → GEO_NEAR_2DSPHERE |
| Q4 | parcelas dentro de un evento | parcelas 2dsphere | 9 → 5 | 2 → 8 | 1,0 → 1,3 | COLLSCAN → COLLSCAN + IXSCAN |
| **Q5** | **nodos sin reportar** | **lecturas** | **5.053 → 433** | 1 → 432 | 9,9 → 8,1 | COLLSCAN + EXPRESS_IXSCAN |
| Q6 | humedad de suelo por hora | - | 24 | 0 | 1,5 → 1,8 | CLUSTERED_IXSCAN |
| **Q7** | **litros por parcela y semana** | **riegos** | **563 → 33** | 0 → 33 | 1,6 → 1,2 | **COLLSCAN → IXSCAN** |
| **Q8** | **heladas por departamento** | **alertas** | **57 → 32** | 22 → 32 | 1,8 → 2,1 | **COLLSCAN → IXSCAN** |
| **Q9** | **etapa por grados-día** | **observaciones** | **1.092 → 846** | 420 → 426 | 29,8 → 29,8 | CLUSTERED_IXSCAN |
| Q10 | índice de riesgo de helada | observaciones (por Q9) | 1.127 → 881 | 422 → 428 | 47,1 → 47,8 | CLUSTERED_IXSCAN + COLLSCAN + EXPRESS_IXSCAN |

En negrita, las cuatro que se mejoran con un índice propio. Cómo interpretar cada fila:

- **Q5 (la mejora más grande, 91 % menos):** su `$lookup` a `lecturas` busca la última lectura de cada nodo por `meta.nodo_id`. El índice automático de la serie temporal está sobre `meta` completo, así que no le sirve (1 clave examinada). Con `{meta.nodo_id: 1, ts: -1}` pasa de recorrer todos los grupos de cada nodo a leer 433.
- **Q7 y Q8:** leían la colección entera (COLLSCAN) para devolver 31 y 10 documentos. Con el índice leen solo los suyos. Q8 parece chica (57 → 32) porque incluye los `$lookup` a `parcelas` y `fincas`, que ya usaban `_id`.
- **Q9, Q2 y Q10:** el índice de `observaciones_fenologicas` ahorra unos 245 documentos en cada una, porque Q9 busca la última observación de cada parcela en cada día (1.272 búsquedas). Q2 y Q10 llaman a Q9.
- **Q3:** sin el índice `2dsphere`, `$geoNear` falla ("unable to find index"). Es un índice necesario, no una optimización.
- **Q4:** pasa de COLLSCAN a IXSCAN, pero con 6 parcelas no hay diferencia real (y en tiempo es 0,3 ms más lenta, que es ruido y el costo de consultar el índice).
- **Q1 y Q6:** ya se resolvían bien. `lecturas` es una serie temporal y MongoDB la lee por tiempo (CLUSTERED_IXSCAN), así que 24 a 30 grupos alcanzan para una noche o un día. No hace falta ningún índice.

**Sobre los tiempos:** las diferencias son de 1 o 2 ms y a veces el "después" es más lento (Q4, Q8). Es ruido de medición. Con 563 riegos o 35 alertas la colección cabe en memoria y leerla toda es casi gratis. El índice importa cuando la colección crece (extrapolación lineal, no medida: con 100 veces más riegos, Q7 leería unos 56.300 documentos sin índice contra unos 3.300 con él); lo que se puede afirmar con estos datos es la reducción de documentos examinados, no la del tiempo.

## Experimento: ¿hace falta el índice automático de `lecturas`?

MongoDB crea solo `meta_1_ts_1` en una serie temporal. Se lo borró en la base de pruebas, se midieron las consultas que leen `lecturas` y se lo volvió a crear (en `agrosense` nunca se borra):

| Consulta | Documentos examinados con / sin `meta_1_ts_1` | Tiempo (ms) con / sin |
|---|---|---|
| Q1 | 30 / 30 | 9,6 / 9,8 |
| Q5 | 433 / 433 | 8,1 / 7,7 |
| Q6 | 24 / 24 | 1,8 / 1,8 |
| Q9 | 846 / 846 | 29,8 / 31,5 |

**Conclusión:** ninguna consulta de este proyecto usa `meta_1_ts_1`: el acceso por tiempo propio de la serie temporal ya alcanza. Igual se lo deja, porque lo crea MongoDB, ocupa poco (104 KB) y borrarlo no ahorra nada que valga la pena; es una respuesta a "¿por qué no indexaron `lecturas`?": ya está indexada y solo faltaba el índice de Q5.

## Costo: lo que ocupa cada índice

Un índice no es gratis: ocupa espacio y hace más lenta cada escritura (hay que actualizarlo).

| Colección | Índice | Tamaño | Para |
|---|---|---|---|
| nodos | `ubicacion_2dsphere` | 20,0 KB | Q3 |
| parcelas | `geometria_2dsphere` | 20,0 KB | Q4 |
| eventos_climaticos | `area_2dsphere` | 20,0 KB | Q4 |
| lecturas | `meta.nodo_id_1_ts_-1` | 112,0 KB | Q5 |
| riegos | `parcela_id_1_inicio_1` | 28,0 KB | Q7 |
| alertas | `tipo_1_inicio_1` | 20,0 KB | Q8 |
| observaciones_fenologicas | `parcela_id_1_fecha_-1` | 20,0 KB | Q9 |
| lecturas | `meta_1_ts_1` (automático) | 104,0 KB | referencia |

Los cuatro índices de rendimiento suman unos 180 KB. El de `lecturas` es el único que toca la colección grande y cada lectura nueva tiene que actualizarlo (no se midió cuánto cuesta); por eso `crear_indices.py` se corre después de `simulator.generar`, que carga toda la temporada de una vez.

## Qué índices NO se crean y por qué

| Candidato | Motivo |
|---|---|
| `alertas {estado, tipo}` (propuesto en `modelo-datos.md`) | Ninguna consulta filtra por `estado`; Q8 filtra por `tipo`. Sin medición que lo justifique no se crea |
| `alertas {parcela_id, inicio}` (propuesto en `modelo-datos.md`) | Q8 no filtra por parcela. Se reevalúa cuando exista la pantalla de alertas del dashboard |
| Otro índice en `lecturas` (por parcela o por finca) | Q1, Q6, Q9 y Q10 ya usan CLUSTERED_IXSCAN con 24 a 1.100 grupos examinados |
| Índices en `fincas`, `parcelas` (por `finca_id`) o `variedades` | Colecciones de 1 a 6 documentos |

## Cómo reproducirlo

```bash
python -m db.indexes.medir_indices            # imprime las tablas de arriba (usa agrosense_tests, ~10 s)
python -m db.indexes.probar_indices           # 19 casos: planes, mejoras y que ningún resultado cambia
python -m db.indexes.crear_indices            # crea los índices en la base de AGROSENSE_BD (por defecto agrosense)
```

`medir_indices` borra y crea índices, por eso trabaja siempre sobre `agrosense_tests`. Los números de tiempo dependen de la computadora; los de documentos examinados deberían repetirse.
