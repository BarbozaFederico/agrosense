# ADR-012: Cierre de supuestos del seed y del simulador

**Estado:** Aceptado (19/10/2026). Cierra los pendientes de [ADR-004](ADR-004-temporada-malbec.md), [ADR-005](ADR-005-parametros-simulacion.md), [ADR-009](ADR-009-temperatura-sospechosa-y-noche-extrema.md), [ADR-010](ADR-010-seed-base.md) y [ADR-011](ADR-011-umbrales-de-riego.md), y fija los parámetros del simulador.

## Contexto

Quedaban unas 60 marcas "a validar" en código y documentos. Con la entrega el 28/10/2026 no hay tiempo para buscar fuentes de cada dato. Se decidió cerrar cada pendiente con un **supuesto adoptado** o una opción propuesta, explicado y registrado, para poder defenderlo en la evaluación.

## Decisiones

### Convención

| # | Tema | Decisión |
|---|---|---|
| 1 | Marcas de un dato | Solo dos categorías: **con fuente** y **supuesto adoptado** (decisión del equipo por falta de datos o de tiempo, con su ADR). Desaparece "a validar". Se reescribe la regla de `CLAUDE.md` |

### Datos del seed

| # | Tema | Decisión | Descartadas |
|---|---|---|---|
| 2 | Límite de "sospechoso" de Tupungato | **−5,6 °C**, calculado: el récord de setiembre de San Rafael (−4,5 °C) es 1,7 °C más cálido que su mínima anual media (−6,2 °C); la misma diferencia aplicada a La Consulta (−7,3 °C, FAUBA, la estación más cercana del Valle de Uco) da −5,6 °C. **Supuesto adoptado** | −4,5 °C (copia de San Rafael: ignora que el Valle de Uco es más frío); −7,3 °C (es una mínima anual, no de setiembre) |
| 3 | Noche extrema de San Rafael | Piso de **−6,3 °C** en el sensor; **5/10/2026 de 03:00 a 08:00** hora de Argentina (06:00 a 11:00 UTC). El simulador calibra el clima de setiembre de San Rafael para que la parcela llegue a los 70 grados-día antes del 2/10 (el SMN da unos 66 en setiembre) y esté en BBCH 07 o más esa noche | −8,3 °C tal cual la prensa (probablemente es nivel del cultivo); fecha del 3/10 (muy justa con la brotación) |
| 4 | Supuestos de diseño sin fuente | Todos **adoptados**: Δ = 2 °C; cortes del índice de riesgo (margen 2 °C, 2 h, aire seco bajo 60 %); 70 grados-día hasta la brotación, corte de 35 y etapas interpoladas (ADR-010); parcelas de 2 ha, espaldero, 4.000 plantas/ha; gravas del 30 % y loamy sand para el pedregoso (ADR-011); coordenadas y altitudes ficticias | Revisarlos uno por uno (no aparecerían datos nuevos) |

### Parámetros del simulador

| # | Tema | Decisión |
|---|---|---|
| 5 | Humedad del aire | Punto de rocío fijo por mes (SMN para San Rafael y San Martín; tabla supuesta de `vid-malbec.md` para Tupungato). La humedad se calcula en cada instante con la fórmula de Magnus según la temperatura: sube cuando hace frío |
| 6 | Heladas | **8 noches finca-noche**: San Rafael 3 (2 en setiembre y la extrema), San Martín 2 (después de la brotación estimada, ~18/9), Tupungato 3 (2 en setiembre y 1 en octubre). Cada finca con sus fechas |
| 7 | Alertas de helada | **5 abren alerta** (riesgo "alto": el brote ya cruzó el umbral) y **3 quedan cerca sin cruzarlo** (Q10: 2 "medio" y 1 "bajo"). Calendario propuesto abajo |
| 8 | Riego | Surco: 76 mm cada 7 días, 2 h desde las 10:00 hora de Argentina, parcelas de la finca en días distintos; extra por alerta de 76 mm. Goteo: setiembre 1,5 mm/día, octubre 1,5, noviembre 2,5, diciembre a febrero 3,5, marzo 2,5, un riego diario de 4 h desde las 08:00; extra por alerta de 4 mm. Octubre y verano tienen fuente; el resto es interpolado y la duración del goteo es supuesto |
| 9 | Humedad de suelo | Secado por mes: al regar sube a la capacidad de campo y baja una cantidad de puntos por día que depende del mes y del suelo, calibrada para que en verano cruce el umbral entre dos turnos y salte la alerta de riego. No usa ETo ni Kc |
| 10 | Nodos | Desvío fijo por nodo de ±0,3 °C y ±1,5 puntos de humedad del aire, más ruido gaussiano en cada lectura (σ = 0,2 °C y 0,5 puntos). Semilla fija `2026` |
| 11 | Fallas de nodos | 5 cortes de reporte de 1 a 12 h repartidos en distintos nodos y meses, y un nodo en `mantenimiento` sin lecturas durante dos semanas (para Q5 y la pantalla de estado) |
| 12 | Clima diario | Máxima y mínima normales del mes (SMN, y DACC para Tupungato) más una variación de unos 2 °C que persiste un par de días; curva de Parton y Logan dentro del día. Las heladas se fuerzan en las noches elegidas |
| 13 | Noche de helada | Enfriamiento de menos de 1 °C por hora después de las primeras 2 h; mínima al amanecer (~07:15 en setiembre y ~06:45 en octubre); entre 3 y 5 horas bajo 0 °C |
| 14 | Observaciones fenológicas | 42: una por parcela el día 15 de cada mes, de setiembre a marzo. La etapa es la de Q9 salvo en 2, que difieren en una etapa y muestran que la observación manda (ADR-004). El observador alterna entre `tecnico` y `encargado` |
| 15 | Fecha de referencia inicial del dashboard | **5/10/2026 06:30** hora de Argentina, con la alerta de la noche extrema abierta |

## Calendario propuesto de las 8 noches (las fechas exactas las fija el simulador)

| Finca | Noche | Mínima del sensor | Resultado |
|---|---|---|---|
| San Rafael | 5/10 (extrema) | −6,3 °C | Alerta |
| San Rafael | 1 en setiembre | ≈ −4,3 °C | Alerta (yema hinchada, umbral −6,1 °C del brote) |
| San Rafael | 1 en setiembre | ≈ −3 °C | Sin cruzar, riesgo "medio" |
| San Martín | 1 después del 18/9 | ≤ −2 °C | Alerta (brotación, umbral −3,9 °C) |
| San Martín | 1 después del 18/9 | ≈ −1 °C | Sin cruzar, riesgo "medio" |
| Tupungato | 1 en setiembre | ≈ −4,5 °C | Alerta (yema hinchada) |
| Tupungato | 1 en setiembre | ≈ −1,5 °C | Sin cruzar, riesgo "bajo" |
| Tupungato | 1 en octubre, después de la brotación (~3/10) | ≤ −2 °C | Alerta |

Ningún valor supera el límite de "sospechoso" de su departamento, salvo la noche extrema de San Rafael (ADR-009).

## Consecuencias

- `configuracion.sospechoso_minimo_c.tupungato` pasa de `None` a −5,6; el simulador ya puede generar heladas en Tupungato. El esquema sigue aceptando `None` y el simulador sigue fallando con un mensaje claro si algún límite queda vacío.
- Se reescribe la regla de marcas de `CLAUDE.md` y se reemplazan las marcas "a validar" por "supuesto adoptado" en código y documentos. Las investigaciones de `docs/investigacion/` quedan como registro de lo que se encontró en su momento.
- Una alerta de helada abierta siempre cierra con riesgo "alto" (el brote ya cruzó el umbral); los niveles "bajo" y "medio" solo se ven en Q10, en noches que no cruzan el umbral. Es consecuencia de la definición de ADR-005.
- Todo lo de esta ADR vale para el MVP del 28/10/2026. Si hubiera más datos después, se cambian en `configuracion`, en `db/seeds/` o en los parámetros del simulador, sin tocar las consultas.
