# Consultas Q1 a Q10

**Estado:** implementadas y probadas (20/10/2026). Decisiones en [ADR-014](decisions/ADR-014-consultas-en-python.md). Código en [`db/queries/`](../db/queries/).

Todas son **consultas de agregación** (`aggregate`) escritas en Python con `pymongo`. Se corren sobre la base `agrosense` (por defecto) desde la raíz del repo con `python -m`. Cada una:

- tiene su pregunta y su requisito en el comentario inicial del archivo;
- expone `pipeline(...)` (la lista de etapas), `consultar(bd, ...)` (la ejecuta; la usa el dashboard) y `main()` (la consola);
- puede mostrar su versión de `mongosh` con `--mongosh`, para pegarla en la consola de MongoDB o en Compass.

## Para entender una agregación

Una agregación es una **tubería**: los documentos entran por un lado y pasan por etapas; cada etapa recibe lo que dejó la anterior. Nada se modifica.

| Etapa | Qué hace | Ejemplo en este proyecto |
|---|---|---|
| `$match` | Filtra documentos | Las lecturas de una noche |
| `$group` | Agrupa y calcula (suma, promedio, mínimo...) | Mínima de cada parcela |
| `$lookup` | Une con otra colección (como un JOIN) | De una alerta a su parcela y a su finca |
| `$set` / `$project` | Agrega, calcula o elige campos | Temperatura del brote = mínima − Δ |
| `$sort`, `$limit` | Ordena, corta | El nodo más cercano |
| `$setWindowFields` | Calcula sobre "ventanas" de documentos ordenados | Suma acumulada, tiempo acumulado |
| `$geoNear`, `$geoIntersects` | Consultas por posición en la Tierra | Nodos cercanos, parcelas dentro de un evento |

El mismo `pipeline` lo ejecuta el servidor igual lo mande `pymongo` o `mongosh`. Eso lo comprueba la prueba automática con Q1, Q4 y Q7.

## Reglas comunes ([ADR-014](decisions/ADR-014-consultas-en-python.md))

| Tema | Regla |
|---|---|
| "Una noche" | La de la mañana `D`: de las 18:00 del día anterior a las 12:00 de `D`, hora de Argentina (UTC−3). Por defecto `2026-10-05` |
| "Ahora" (Q5 y Q6) | Es un parámetro (ADR-004). Por defecto `2026-10-05T09:30Z` (06:30 hora de Argentina) |
| Semana (Q7 y Q8) | De lunes a domingo, hora de Argentina |
| Temperatura de una parcela | La del nodo **más frío** en cada instante (igual que las alertas). El brote está `Δ = 2 °C` más frío que el sensor |
| Etapa fenológica | **Estimada** por grados-día para los cálculos de helada (Q2 y Q10). Q9 informa además la observada y la efectiva |
| Configuración | Δ, minutos de nodo inactivo, cortes del riesgo y umbrales de riego se leen de la base, no del código |

## Q9 - Etapa fenológica por grados-día

**Pregunta:** ¿en qué etapa fenológica estimada está cada parcela? **Requisito:** RF-16, RF-18. **Técnica:** `$group` + `$setWindowFields` (suma acumulada) + `$lookup`. **Archivo:** `q9_etapa_por_grados_dia.py`.

1. `$match`: lecturas hasta el fin de la fecha pedida.
2. `$group` por parcela, nodo y día local (`$dateTrunc`, zona −03:00): máxima y mínima.
3. `$group` por parcela y día: promedio de los 2 nodos.
4. `$lookup` a `parcelas` y a `variedades`: base (10 °C), tope (32 °C), brotación (70 GD) y etapas.
5. `$set`: grados-día del día = `max(0, min((Tmáx + Tmín)/2, tope) − base)`.
6. `$setWindowFields`: suma de los días anteriores (`documents: [unbounded, -1]`) = grados-día acumulados hasta ayer.
7. `$filter` + `$last`: la última etapa cuyo `gd_desde_brotacion` no supera lo acumulado menos los 70 de la brotación.
8. `$lookup` a `observaciones_fenologicas`: la última observación hasta ese día.
9. `$project`: devuelve la estimada, la observada y la efectiva (la observada si existe, si no la estimada).

**Resultado real (5/10/2026):** San Rafael y Tupungato en Brotación (umbral −3,9 °C), San Martín en Hojas desplegadas (sin umbral). El 15/10, `P-SR-1` tiene etapa estimada 16 y observada 53: manda la observada.
**Cómo se verifica:** las 1.272 filas (6 parcelas × 212 días) tienen la misma etapa que calculó el simulador, y los grados-día difieren menos de 0,01. Tarda ~0,5 s.
**Para defenderla:** es la misma regla que el simulador, por eso Q9 y las alertas guardadas nunca se contradicen.

## Q10 - Índice de riesgo de helada

**Pregunta:** ¿qué riesgo tuvo cada parcela en cada noche? **Requisito:** RF-19. **Técnica:** `$group` + `$setWindowFields` + `$lookup`. **Archivo:** `q10_riesgo_de_helada.py`.

1. Etapa estimada y umbral de cada parcela (Q9).
2. `$group` por parcela e instante: nodo más frío y humedades. El aire cuenta solo entre las 22:00 y las 08:00.
3. `$setWindowFields` con `$integral`: horas con el brote a menos de 1 °C del umbral.
4. `$group` por parcela: mínima, horas, humedad media del aire y del suelo.
5. Margen = mínima del brote − umbral. Nivel base: **alto** si ≤ 0, **medio** si ≤ 2, **bajo** si más.
6. Agravantes: duración (≥ 2 h cerca del umbral), aire seco (< 60 %) y suelo seco (bajo el umbral de riego). Cada uno sube un nivel (el de suelo solo de bajo a medio), con tope "alto". No es un porcentaje de daño.

**Resultado real:**

| Noche | Parcela | Margen | Nivel |
|---|---|---|---|
| 8/9 | Tupungato | +7,0 °C | bajo |
| 15/9 | San Martín | +1,3 °C | medio |
| 21/9 | San Rafael | +1,23 y +1,16 °C | medio |
| 5/10 | San Rafael | −4,40 y −4,27 °C | alto (duración) |

**Cómo se verifica:** en las 5 noches con alerta da "alto" con el mismo margen que guarda `alertas.riesgo` (±0,01 °C); en las 3 sin alerta da el nivel buscado.
**Limitación conocida:** una noche muy cálida y muy seca (San Martín el 21/9, aire al 39 %) sube a "medio" por "aire seco" aunque no haya frío. Es la regla de ADR-005 aplicada al pie de la letra.

## Q2 - Parcelas con mínima bajo el umbral de su etapa

**Requisito:** RF-01, RF-04. **Técnica:** `$group` + `$lookup` (lecturas → parcelas → fincas). **Archivo:** `q2_minima_bajo_umbral.py`.

1. Etapa estimada y umbral de cada parcela (Q9).
2. `$match` + `$group`: mínima de cada parcela en la noche.
3. `$set`: mínima del brote y su umbral (con `$getField` sobre un diccionario con los umbrales).
4. `$match`: solo las que quedaron bajo el umbral.
5. `$lookup` a `parcelas` y `fincas`: nombre y departamento.

**Resultado real:** el 5/10 devuelve `P-SR-1` (margen −4,40 °C) y `P-SR-2` (−4,27 °C); el 29/9, `P-SM-1` y `P-SM-2`; el 21/9 (noche "medio") no devuelve nada.
**Cómo se verifica:** en cada una de las 8 noches devuelve exactamente las parcelas que abrieron alerta esa noche.

## Q1 - Horas bajo 0 °C por parcela

**Requisito:** RF-03, RF-04. **Técnica:** `$group` + `$setWindowFields` con `$integral`. **Archivo:** `q1_horas_bajo_cero.py`.

1. `$match`: lecturas de la noche.
2. `$group` por parcela e instante: temperatura del nodo más frío.
3. `$setWindowFields`: integra un indicador (1 si hace menos de 0 °C, 0 si no) a lo largo del tiempo, en horas. Cada lectura bajo cero aporta 5 minutos.
4. `$group`: el total de la noche es el último valor acumulado.

**Resultado real (5/10):** `P-SR-1` y `P-SR-2` 8,17 h (mínimas −6,30 y −6,17 °C). Otras noches: Tupungato 22/9, 5,7 h; San Rafael 21/9, 3,5 h.
**Cómo se verifica:** contra un conteo aparte en Python (lecturas con el nodo más frío bajo cero × 5 min), diferencia máxima de 0,003 h.

## Q5 - Nodos sin reportar

**Requisito:** RF-06. **Técnica:** `$lookup` (nodos → lecturas) + `$match`. **Archivo:** `q5_nodos_sin_reportar.py`.

1. Se parte de `nodos`, así un nodo sin ninguna lectura también aparece.
2. `$lookup` a `lecturas` con `pipeline`: la última lectura hasta el "ahora" (`$sort` descendente y `$limit: 1`).
3. `$set`: minutos desde esa lectura.
4. `$match`: más que `configuracion.nodo_inactivo_min` (30), o sin lecturas.

**Resultado real:** `--ahora 2026-11-12T21:00:00Z` → `N-SR-1-A`, 245 min (corte de 6 h); `--ahora 2027-03-31T12:00:00Z` → `N-TU-2-B` (mantenimiento); el 5/10 06:30 → ninguno.

## Q6 - Humedad de suelo por hora

**Requisito:** RF-03. **Técnica:** `$match` + `$group` con `$dateTrunc`. **Archivo:** `q6_humedad_suelo_horaria.py`.

1. `$match`: las 24 horas completas anteriores a la hora en curso, de una parcela.
2. `$group` por hora local: promedio de la humedad de suelo de los 2 nodos.
3. `$sort`.

**Resultado real:** 24 filas, con 24 lecturas cada una (2 nodos × 12), por ejemplo `P-SR-1` el 19/1 de 12:00 a 15:00: 19,70, 19,64, 19,64, 19,59 %.

## Q3 - Nodos más cercanos a un punto

**Requisito:** RF-07. **Técnica:** `$geoNear`. **Archivo:** `q3_nodos_cercanos.py`. Necesita el índice `2dsphere` de `nodos.ubicacion` (`python -m db.indexes.crear_indices`).

`$geoNear` va **primero** en la tubería y devuelve los documentos del más cercano al más lejano, con la distancia en metros. Se hace sobre `nodos` y no sobre `lecturas` porque las series temporales solo aceptan índices de puntos y no devuelven la distancia.

**Resultado real (centro de `P-SR-1`):** `N-SR-1-A` y `N-SR-1-B` a 50,0 m, `N-SR-2-B` a 130,9 m, `N-SR-2-A` a 200,0 m. Verificado contra una distancia calculada aparte (haversine).

## Q4 - Parcelas dentro de un evento climático

**Requisito:** RF-07, RF-08. **Técnica:** `$geoIntersects`. **Archivo:** `q4_parcelas_en_evento.py`.

Se lee el evento (su polígono `area`) y se buscan las parcelas cuyo polígono se cruza con él. "Dentro" se interpreta como "toca o está dentro".

**Resultado real:** el evento de la noche extrema (5/10, 03:00 a 08:00) alcanza `P-SR-1` y `P-SR-2` y ninguna otra.

## Q7 - Litros regados por parcela y semana

**Requisito:** RF-05. **Técnica:** `$group` con `$dateTrunc` (semana). **Archivo:** `q7_litros_por_semana.py`.

Los litros ya están en cada riego (lámina × superficie × 10.000); la consulta los suma por parcela y semana (lunes a domingo, hora de Argentina). Versión de `mongosh` (resumida):

```js
db.riegos.aggregate([
  { $match: { parcela_id: "P-SR-1" } },
  { $group: { _id: { parcela: "$parcela_id",
                     semana: { $dateTrunc: { date: "$inicio", unit: "week", startOfWeek: "monday", timezone: "-03:00" } } },
              litros: { $sum: "$litros" }, riegos: { $sum: 1 } } },
  { $sort: { "_id.semana": 1 } }
])
```

**Resultado real:** `P-SR-1` riega 1.520.000 L por semana (un turno de 76 mm en 2 ha). Total de la temporada: San Rafael 100.320.000 L, San Martín 103.360.000 L y Tupungato 22.760.000 L.

## Q8 - Heladas por departamento y semana

**Requisito:** RF-04, RF-08. **Técnica:** `$group` + `$lookup` (alertas → parcelas → fincas). **Archivo:** `q8_heladas_por_departamento.py`.

Las alertas guardan solo la parcela (ADR-003); el departamento sale de dos `$lookup` encadenados. Un "evento" es una alerta de helada: una noche con alerta en una finca de 2 parcelas cuenta 2 alertas y 2 parcelas afectadas.

| Semana (lunes) | Departamento | Alertas | Parcelas | Mínima del brote |
|---|---|---|---|---|
| 21/9 | Tupungato | 2 | 2 | −6,67 °C |
| 28/9 | San Martín | 2 | 2 | −3,12 °C |
| 28/9 | San Rafael | 2 | 2 | −4,53 °C |
| 5/10 | San Rafael | 2 | 2 | −8,30 °C |
| 5/10 | Tupungato | 2 | 2 | −3,03 °C |

## Índices que usa cada consulta

| Consulta | Índice | Mejora |
|---|---|---|
| Q1, Q6 | Ninguno propio: la serie temporal se lee por tiempo (CLUSTERED_IXSCAN) | - |
| Q2, Q9, Q10 | `observaciones_fenologicas {parcela_id, fecha}` | 1.092 → 846 documentos examinados (Q9) |
| Q3, Q4 | `2dsphere` en `nodos` y `parcelas` | Q3 no funciona sin el índice |
| Q5 | `lecturas {meta.nodo_id, ts}` | 5.053 → 433 |
| Q7 | `riegos {parcela_id, inicio}` | 563 → 33 |
| Q8 | `alertas {tipo, inicio}` | 57 → 32 |

Se crean con `python -m db.indexes.crear_indices`. Mediciones completas, costo en espacio y experimentos en [`performance.md`](performance.md) y [ADR-015](decisions/ADR-015-indices-de-rendimiento.md).

## Cómo se probó

`python -m db.queries.probar_consultas` (43 casos, base `agrosense_tests`, ~30 s): cada consulta se compara con un cálculo independiente (Python con `find`, el escenario del simulador o la colección `alertas`) y el texto de `mongosh` de Q1, Q4 y Q7 se ejecuta en `mongosh` y se compara con el resultado de Python. Detalle de lo que verifica cada caso en la salida de la prueba.

## Consultas de apoyo del dashboard

La pantalla "Resumen de la mañana" (ADR-018) reutiliza Q5, Q9 y Q10 y suma cuatro consultas de `db/queries/resumen_manana.py`. **No son Q11**: no responden a un requisito nuevo, solo traen lo que la pantalla muestra. Ninguna escribe en la base.

| Función | Qué devuelve | Etapas |
|---|---|---|
| `alertas_de_helada` | Alertas de helada que se solapan con la noche (de las 18:00 a las 12:00, hora de Argentina) | `$match` (`inicio` antes del cierre y `fin` nulo o posterior al comienzo), `$project`, `$sort` |
| `ultimo_riego` | El último riego de cada parcela que empezó antes del cierre de la noche | `$match`, `$sort` descendente, `$group` con `$first`, `$project` |
| `ultima_lectura` | Momento de la última lectura hasta un "ahora" (se busca solo en las 6 horas previas) | `$match` por rango de `ts`, `$sort`, `$limit` 1 |
| `noches_con_helada` | Las mañanas con al menos una alerta de helada (la mañana de una alerta es la fecha local de `inicio` + 6 h) | `$match`, `$group` con `$dateToString` y `$dateAdd`, `$sort` |

Cada una tiene su `pipeline_xxx(...)`, de donde sale el texto de `mongosh` del panel "Ver consulta". Se prueban con `python -m dashboard.probar_datos`.

La pantalla "Detalle de parcela" (ADR-019) reutiliza Q1, Q6, Q7, Q9 y Q10 y suma dos consultas de `db/queries/detalle_parcela.py`, tampoco Q11:

| Función | Qué devuelve | Etapas |
|---|---|---|
| `curva_de_la_noche` | La temperatura de cada nodo de la parcela cada 5 minutos, de las 18:00 a las 12:00 (216 lecturas por nodo) | `$match` por parcela y rango de `ts`, `$project`, `$sort` por hora |
| `riegos_recientes` | Los últimos riegos de la parcela que empezaron antes del cierre de la noche | `$match`, `$sort` descendente, `$limit`, `$project` |

Se prueban con `python -m dashboard.probar_detalle`.

La pantalla "Alertas" (ADR-020) reutiliza Q8 y suma tres consultas de `db/queries/alertas_pantalla.py`, tampoco Q11:

| Función | Qué devuelve | Etapas |
|---|---|---|
| `alertas_de_la_noche` | Las alertas de ambos tipos que se solapan con la noche (de las 18:00 a las 12:00) | `$match` (`inicio` antes del cierre y `fin` nulo o posterior al comienzo), `$project`, `$sort` |
| `historial` | Las últimas alertas (hasta 200) que empezaron antes del cierre de la noche, las más recientes primero | `$match`, `$sort` descendente, `$limit`, `$project` |
| `etapas_del_malbec` | Nombre y rango BBCH de cada etapa, para traducir el número que guarda la alerta | `find` sobre `variedades` |

Se prueban con `python -m dashboard.probar_alertas`.

La pantalla "Estado de nodos" (ADR-021) reutiliza Q5 y suma una consulta de `db/queries/estado_nodos.py`, tampoco Q11:

| Función | Qué devuelve | Etapas |
|---|---|---|
| `ultimo_reporte` | Los 12 nodos con el momento de su última lectura hasta el "ahora" y los minutos desde entonces | Las 3 primeras etapas de Q5 (`$lookup` a la última lectura y los dos `$set`), `$project`, `$sort` |

Q5 devuelve solo los nodos que no reportan; esta trae todos, con la misma búsqueda. Se prueba con `python -m dashboard.probar_nodos`, que compara los nodos sin reportar contra Q5 en 75 fechas de la temporada.
