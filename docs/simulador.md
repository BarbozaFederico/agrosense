# Simulador

**Estado:** implementado (19/10/2026). Decisiones en [ADR-004](decisions/ADR-004-temporada-malbec.md), [ADR-005](decisions/ADR-005-parametros-simulacion.md), [ADR-012](decisions/ADR-012-cierre-de-supuestos.md) y [ADR-013](decisions/ADR-013-diseno-del-simulador.md). Código en [`simulator/`](../simulator/).

## Qué genera

Una temporada de Malbec (1/9/2026 a 31/3/2027) para los 12 nodos, con una lectura cada 5 minutos, y todo lo que se deriva de ella:

| Colección | Cantidad | Detalle |
|---|---|---|
| `lecturas` | 727.980 | 12 nodos × 61.056 lecturas = 732.672, menos 4.692 por cortes de reporte (372) y por un nodo en mantenimiento (4.320) |
| `alertas` (helada) | 10 | 5 noches con alerta × 2 parcelas; todas cerradas, con riesgo "alto" |
| `alertas` (riego) | 25 | 4 a 6 por parcela de surco, 2 a 3 por parcela de goteo |
| `riegos` | 563 | 545 de turno (121 de surco y 424 de goteo) y 18 extra por alerta de riego |
| `observaciones_fenologicas` | 42 | una por parcela el día 15 de cada mes; 2 difieren de la etapa estimada |

Los datos son sintéticos y no representan fincas reales. Todo lleva `fuente: "simulado"` (las observaciones, `"seed"`).

## Cómo se usa

Desde la raíz del repo, con el entorno virtual activado:

```bash
python -m db.seeds.cargar          # requisito: fincas, parcelas, nodos y configuración
python -m simulator.generar        # genera e inserta la temporada (unos 25 segundos)
python -m simulator.probar_simulador   # pruebas con salida real (unos 55 segundos)
```

Para otra base, en Git Bash: `AGROSENSE_BD=agrosense_tests python -m simulator.generar`. Se puede repetir: la temporada sale exactamente igual (semilla `2026`) y solo reemplaza lo suyo. No toca nada con `escenario_id`. Al terminar corre la auditoría de `lecturas` (0 mal formadas y 0 sospechosas inesperadas).

Los módulos se pueden importar desde otro código (por ejemplo, la simulación en vivo del dashboard, RF-14):

| Módulo | Para qué sirve |
|---|---|
| `parametros.py` | Constantes: normales, puntos de rocío, tasas de secado, riegos |
| `calendario.py` | Las 8 noches de helada, los cortes de nodos y las observaciones que corrigen al modelo |
| `clima.py` | Temperatura y humedad del aire: astronomía, Parton y Logan, noche de helada, Magnus |
| `fenologia.py` | Grados-día y etapa BBCH (la regla de Q9) |
| `escenario.py` | Arma el clima, los nodos y las etapas de toda la temporada, sin base de datos |
| `riego.py` | Riegos de turno, humedad de suelo y alertas de riego |
| `alertas.py` | `Detector` (regla de alerta), índice de riesgo y alertas de helada |
| `generar.py` | Orquesta: simula, valida, borra lo anterior, inserta y audita |
| `probar_simulador.py` | Las pruebas |

## Decisiones

| Tema | Valor |
|---|---|
| Período simulado | 1/9/2026 a 31/3/2027 (temporada completa; no copia datos reales) |
| Variedad | Malbec en las 6 parcelas; "variedad simulada X" opcional |
| Noches de helada | 8 (San Rafael 3, San Martín 2, Tupungato 3), cada finca con sus fechas; una es la noche precargada |
| Riego | Mixto: turnos fijos más riegos extra cuando se abre la alerta de riego. San Rafael y San Martín por surco (76 mm cada 7 días); Tupungato por goteo (1,5 a 3,5 mm/día). Ver [ADR-005](decisions/ADR-005-parametros-simulacion.md) |
| Suelo | San Rafael franco; San Martín franco arenoso; Tupungato pedregoso ([ADR-011](decisions/ADR-011-umbrales-de-riego.md)) |
| Clima | Normales SMN (San Rafael, San Martín) y El Peral DACC (Tupungato); ver `investigacion/verificacion-fuentes.md` |
| Heladas | Las mínimas del sensor no pasan el límite de "sospechoso" de su departamento (San Rafael −4,5 °C, San Martín −2,8 °C, Tupungato −5,6 °C); la mínima ocurre al amanecer. Si el límite de un departamento es `None`, el simulador **falla con un mensaje claro** ([ADR-009](decisions/ADR-009-temperatura-sospechosa-y-noche-extrema.md)) |
| Noche extrema | La noche precargada (RF-13) es la única que puede superar ese límite, solo en San Rafael: 5/10/2026, piso de −6,3 °C en el sensor (supuesto adoptado, ADR-012). Dura ~7 h bajo cero (excepción, ADR-013) |
| Fincas | San Rafael, Tupungato y San Martín (ficticias) |
| Etapas fenológicas | Escala BBCH; grados-día base 10 °C desde el 1/9: 260 de brotación a floración y 712 de floración a envero (Zapata 2017); etapas intermedias repartidas en forma pareja (supuesto) |

> **Hora de referencia:** Q5 (últimos 30 minutos) y Q6 (últimas 24 horas) reciben la fecha "ahora" como parámetro, elegida con un selector en el dashboard (ADR-004). Las fechas del seed no se desplazan. El dashboard abre el 5/10/2026 06:30 (hora de Argentina), con la alerta de la noche extrema abierta (ADR-012).

## Parámetros

Fijados en [ADR-012](decisions/ADR-012-cierre-de-supuestos.md) y [ADR-013](decisions/ADR-013-diseno-del-simulador.md); todos supuestos adoptados, salvo donde se indica fuente.

| Parámetro | Valor |
|---|---|
| Semilla | `2026` (la temporada sale igual en cada corrida) |
| Clima diario | Máxima y mínima normales del mes (SMN, DACC para Tupungato) más una anomalía común de ~2 °C que persiste un par de días (AR(1), 0,6) y variación propia de 0,8 °C; curva de Parton y Logan. Los días comunes nunca bajan de 1,5 °C |
| Humedad del aire | Punto de rocío fijo por mes (SMN; derivado para Tupungato) con variación diaria; humedad con la fórmula de Magnus según la temperatura |
| Noche de helada | Enfriamiento rápido las primeras 2 h y después de menos de 0,95 °C/h; mínima al amanecer (~07:00 en octubre, ~07:20 en setiembre); 3 a 5 h bajo cero (extrema: 7 h) |
| Nodos | Desvío fijo de ±0,3 °C y ±1,5 puntos de humedad del aire (±0,4 puntos de humedad de suelo) entre gemelos; ruido gaussiano de 0,2 °C, 0,5 puntos y 0,1 puntos |
| Fallas | 5 cortes de reporte de 1 a 12 h y un nodo (`N-TU-2-B`) en `mantenimiento` sin lecturas desde el 17/3 |
| Riego por surco | 76 mm cada 7 días, 2 h desde las 10:00 (hora de Argentina); las dos parcelas de cada finca en días distintos; extra por alerta de 76 mm |
| Riego por goteo | Setiembre y octubre 1,5 mm/día, noviembre y marzo 2,5, diciembre a febrero 3,5; 4 h diarias desde las 08:00; extra de 4 mm |
| Humedad de suelo | Sube a la capacidad de campo al regar y baja por día según mes, suelo y calor. Franco 25 %, franco arenoso 23 %, pedregoso 10,5 % de capacidad de campo (ADR-011) |
| Observaciones | 42 (una por parcela el día 15 de cada mes), 2 que corrigen a Q9 |

## Calendario de las 8 noches

Fechas fijadas en `simulator/calendario.py` y verificadas por las pruebas. Cada una cae a 2 días o más del cambio de etapa (las heladas corren unos grados-día esos cambios y el escenario repite hasta estabilizarse).

| Finca | Mañana | Etapa | Mínima del nodo más frío | Resultado |
|---|---|---|---|---|
| Tupungato | 8/9 | Yema dormida | −1,6 °C | Sin cruzar, riesgo "bajo" (Q10) |
| San Martín | 15/9 | Yema hinchada | −2,8 °C | Sin cruzar, riesgo "medio" |
| San Rafael | 21/9 | Yema hinchada | −2,9 °C | Sin cruzar, riesgo "medio" |
| Tupungato | 22/9 | Yema hinchada | −4,7 °C | Alerta |
| San Martín | 29/9 | 2 a 5 hojas | −1,1 °C | Alerta |
| San Rafael | 2/10 | Brotación | −2,5 °C | Alerta |
| San Rafael | 5/10 | Brotación | −6,3 °C | Alerta (noche extrema) |
| Tupungato | 10/10 | 2 a 5 hojas | −1,0 °C | Alerta |

## Regla de grados-día y etapa (la misma que usará Q9)

1. Grados-día de un día = `max(0, min((Tmáx + Tmín) / 2, 32) − 10)`, desde el 1/9.
2. Tmáx y Tmín del día de una parcela = promedio de las de sus 2 nodos, sobre el día local (hora de Argentina, UTC−3).
3. La etapa de un día usa los grados-día acumulados hasta el día **anterior**, menos los 70 grados-día hasta la brotación.
4. De ahí sale la última etapa de `variedades.etapas` cuyo `gd_desde_brotacion` no supera esa cifra. Las alertas y las observaciones guardan el `bbch_desde` de esa etapa.

Con esta regla la brotación estimada es San Martín ~20/9, San Rafael ~30/9 y Tupungato ~4/10. La prueba `cruce con la base` recalcula grados-día y etapa con una agregación sobre `lecturas` (`$group` con `$dateTrunc`) y obtiene las mismas 212 etapas en tres parcelas.

## Cómo se probó

`python -m simulator.probar_simulador` (51 casos, base `agrosense_tests`):

- **Reglas puras:** grados-día, detector de alertas con histéresis, índice de riesgo, astronomía y la curva de helada (enfriamiento máximo 0,95 °C/h tras las primeras 2 h, horas bajo cero y mínima al amanecer).
- **Escenario:** determinismo con la semilla, promedios mensuales contra las normales, brotación por finca, BBCH ≥ 7 en San Rafael el 5/10, resultado de cada una de las 8 noches (margen del brote medido en las lecturas), que no haya otras heladas y que ninguna lectura pase el límite del departamento salvo en la noche extrema.
- **Base:** conteos, auditoría (0 y 0), alertas de helada y de riego, riegos extra que apuntan a su alerta, litros, turnos cada 7 días, nodo en mantenimiento y cortes sin lecturas, observaciones, cruce de etapas con una consulta a `lecturas` y que una segunda carga deje lo mismo.

## Marcas en los datos

- `fuente`: origen del dato (`simulado`; las observaciones, `seed`).
- `escenario_id`: identifica lo generado por una simulación en vivo, para poder borrarlo (el simulador de la temporada no lo usa ni lo toca).
