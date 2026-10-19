# ADR-013: Diseño del simulador y decisiones menores

**Estado:** Aceptado (19/10/2026). Implementa los parámetros de [ADR-012](ADR-012-cierre-de-supuestos.md). Detalle en [`simulador.md`](../simulador.md).

## Contexto

ADR-012 fijó los parámetros del simulador. Al implementarlo hubo que resolver detalles que ese ADR no cubría, y dos cosas resultaron distintas de lo previsto: el calendario de heladas (depende de la etapa de cada finca) y la duración de la noche extrema.

## Decisiones

| # | Tema | Decisión | Motivo |
|---|---|---|---|
| 1 | Noche extrema | **Dura ~7 h bajo cero** y enfría ~0,9 °C/h. Las demás noches: 3 a 5 h bajo cero y menos de 0,95 °C/h | Llegar a −6,3 °C a menos de 1 °C/h no cabe en 5 h (haría falta 1,26 °C/h). Se eligió relajar la duración |
| 2 | Calendario de heladas | Fechas fijas en `calendario.py` (tabla en `simulador.md`), cada una a 2 días o más del cambio de etapa. Reemplaza la tabla orientativa de ADR-012 | Con el brote 2 °C más frío que el sensor, solo hay alerta si la mínima cruza el umbral de la etapa de ese día |
| 3 | Mínima de cada noche | Se calcula con el umbral de la etapa: alerta = umbral + Δ − 0,4 °C; "medio" = umbral + Δ + 1,3 °C; "bajo" = −1,5 °C. El escenario repite hasta que las etapas se estabilicen | Una helada baja unos grados-día y puede correr un cambio de etapa |
| 4 | Tupungato en setiembre | Una sola noche ("bajo", 8/9) y su primera alerta el 22/9 (yema hinchada, desde el 13/9). Tupungato no puede tener alerta antes de ~13/9: su yema está dormida (umbral −10,6 °C) | Corrige ADR-012, que ubicaba la alerta de Tupungato también "en setiembre" sin considerar la etapa |
| 5 | San Martín | No puede haber alerta con la yema hinchada: con su límite de −2,8 °C el brote queda en −4,8 °C, que no cruza −6,1 °C. Por eso su noche de yema hinchada (15/9) queda en riesgo "medio" y su alerta es el 29/9 (2 a 5 hojas) | Mismo motivo |
| 6 | Alertas de helada | Por parcela, con el nodo más frío; **5 noches con alerta × 2 parcelas = 10 alertas**. Se abre al cruzar el umbral y se cierra tras 1 hora seguida por encima (12 lecturas) | Con 15 min el ruido de ±0,2 °C abría varias alertas en una misma noche |
| 7 | Alertas de riego | Por parcela, con el promedio móvil de 1 hora de los dos nodos; el riego extra empieza 3 h después de abrirse. En goteo espera al primer hueco libre; en surco, si un turno está por empezar, no se agrega otro riego | El valor instantáneo oscilaba alrededor del umbral |
| 8 | Etapa del día | Usa los grados-día hasta el día anterior; Tmáx y Tmín del día de la parcela son el promedio de las de sus 2 nodos, sobre el día local (UTC−3) | Es lo que se sabe al empezar el día; es la regla de Q9 |
| 9 | BBCH guardado | Las alertas y las observaciones guardan el `bbch_desde` de la etapa | Un solo número por etapa; Q9 devuelve la etapa |
| 10 | Brotación estimada | San Martín ~20/9, San Rafael ~30/9, Tupungato ~4/10, con la regla de Q9. ADR-009 hablaba de ~1/10 para San Rafael (66 grados-día de la media mensual del SMN, que subestima) | Los 66 grados-día se calcularon con la media mensual |
| 11 | Humedad de suelo | Los mm de cada riego son la lámina bruta de las fuentes; el modelo lleva el suelo a capacidad de campo con cada riego. Goteo: cada día repone entre el 62 y el 82 % de lo perdido el día anterior | El suelo no se seca durante las 4 h del riego (~0,83 de la pérdida diaria): con menos reposición el suelo se aleja de a poco y salta la alerta |
| 12 | Suelo y nodos | Desvío entre gemelos de ±0,4 puntos de humedad de suelo y ruido de 0,1 | Completa ADR-012 decisión 10 |
| 13 | Nodo en mantenimiento | `N-TU-2-B`, sin lecturas desde el 17/3/2027; su `estado` en `nodos` queda en `mantenimiento` (estado actual al cierre de la temporada) | `estado` es administrativo y no cambia en el tiempo |
| 14 | Identificadores | `ObjectId` determinista (fecha, huella de tipo y parcela, número) para alertas, riegos y observaciones | Cada corrida da los mismos `_id`; el esquema exige `_id` antes de insertar |
| 15 | Cobertura de pruebas | `probar_simulador.py`, 51 casos, sin pytest (mismo estilo que `probar_esquemas.py`) | Una sola forma de probar en el repo |

## Consecuencias

- `numpy==2.5.4` pasa a `requirements.txt` (ya venía con Streamlit).
- Las consultas Q9 y Q10 tienen que usar la regla de `docs/simulador.md` (sección "Regla de grados-día y etapa"), así los resultados coinciden con los del simulador. La prueba `cruce con la base` ya lo comprueba con una agregación sobre `lecturas`.
- Una alerta de helada abierta siempre cierra con riesgo "alto" (el brote ya cruzó el umbral); "bajo" y "medio" solo se ven en Q10, en las 3 noches que no cruzan el umbral.
- Los días comunes nunca bajan de 1,5 °C, así que solo las 8 noches designadas tienen temperatura bajo cero.
- Si cambian el clima o las etapas, hay que revisar `calendario.HELADAS`: el escenario falla con un mensaje claro si una fecha cae pegada a un cambio de etapa y no logra estabilizarse.
