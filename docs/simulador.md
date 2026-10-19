# Simulador

**Estado:** esqueleto, se completa en los Sprints A y B.

## Qué genera

- Una temporada de Malbec (1/9/2026 a 31/3/2027) para 12 nodos, 1 lectura cada 5 minutos (unas 732.700 lecturas). Ver [ADR-004](decisions/ADR-004-temporada-malbec.md).
- Escenarios normales y noches de helada distribuidos entre las 3 fincas y las semanas.
- Una noche de helada precargada para el dashboard (RF-13).

## Decisiones

| Tema | Valor |
|---|---|
| Período simulado | 1/9/2026 a 31/3/2027 (temporada completa; no copia datos reales) |
| Variedad | Malbec en las 6 parcelas; "variedad simulada X" opcional |
| Noches de helada | 6 a 8, entre septiembre y noviembre, en distintas etapas; una es la noche precargada |
| Riego | Mixto: turnos fijos más riegos extra cuando se abre la alerta de riego. San Rafael y San Martín por surco (76 mm cada 7 días); Tupungato por goteo (1,5 a 3,5 mm/día). Ver [ADR-005](decisions/ADR-005-parametros-simulacion.md) |
| Suelo | San Rafael franco; San Martín franco arenoso; Tupungato pedregoso |
| Clima | Normales SMN (San Rafael, San Martín) y El Peral DACC (Tupungato); ver `investigacion/verificacion-fuentes.md` |
| Heladas | Las mínimas del sensor no pasan el límite de "sospechoso" de su departamento (`configuracion.sospechoso_minimo_c`: San Rafael −4,5 °C, San Martín −2,8 °C y Tupungato −5,6 °C, ADR-012); la mínima ocurre al amanecer. Si el límite de un departamento es `None`, el simulador **falla con un mensaje claro** en lugar de generar heladas ([ADR-009](decisions/ADR-009-temperatura-sospechosa-y-noche-extrema.md)) |
| Noche extrema | La noche precargada (RF-13) es la única que puede superar ese límite, solo en San Rafael: 5/10/2026 de 03:00 a 08:00 hora de Argentina, justo después de la brotación estimada, con piso de −6,3 °C en el sensor (supuesto adoptado, ADR-012). Se declara en `configuracion.noche_extrema`; el simulador calibra el clima de setiembre y se comprueba con Q9 que la parcela esté en BBCH 07 o más |
| Fincas | San Rafael, Tupungato y San Martín (ficticias) |
| Etapas fenológicas | Escala BBCH; grados-día base 10 °C desde el 1/9: 260 de brotación a floración y 712 de floración a envero (Zapata 2017); etapas intermedias repartidas en forma pareja (supuesto) |

> **Hora de referencia:** Q5 (últimos 30 minutos) y Q6 (últimas 24 horas) reciben la fecha "ahora" como parámetro, elegida con un selector en el dashboard (ADR-004). Las fechas del seed no se desplazan.

> **Observaciones fenológicas:** el seed incluye observaciones manuales precargadas (por ejemplo, una por parcela por mes).

## Parámetros

Fijados en [ADR-012](decisions/ADR-012-cierre-de-supuestos.md) (todos supuestos adoptados, salvo donde se indica fuente):

| Parámetro | Valor |
|---|---|
| Semilla | `2026` (la temporada sale igual en cada corrida) |
| Clima diario | Máxima y mínima normales del mes (SMN, DACC para Tupungato) más variación de ~2 °C con rachas; curva de Parton y Logan |
| Humedad del aire | Punto de rocío fijo por mes; humedad con la fórmula de Magnus según la temperatura |
| Noche de helada | Enfriamiento de menos de 1 °C/h tras las primeras 2 h; mínima al amanecer (~07:15 en setiembre, ~06:45 en octubre); 3 a 5 h bajo 0 °C |
| Heladas | 8 noches: San Rafael 3, San Martín 2, Tupungato 3; 5 abren alerta y 3 quedan cerca del umbral sin cruzarlo |
| Nodos | Desvío fijo de ±0,3 °C y ±1,5 puntos de humedad del aire; ruido gaussiano de 0,2 °C y 0,5 puntos |
| Fallas | 5 cortes de reporte de 1 a 12 h y un nodo en `mantenimiento` durante dos semanas |
| Humedad de suelo | Sube a la capacidad de campo al regar y baja por día según mes y suelo, calibrada para cruzar el umbral en verano |
| Riego por surco | 76 mm cada 7 días, 2 h desde las 10:00 (hora de Argentina); extra por alerta de 76 mm |
| Riego por goteo | Setiembre y octubre 1,5 mm/día, noviembre y marzo 2,5, diciembre a febrero 3,5; 4 h diarias desde las 08:00; extra de 4 mm |
| Observaciones | 42 (una por parcela el día 15 de cada mes), 2 que corrigen a Q9 |
| Fecha inicial del dashboard | 5/10/2026 06:30 hora de Argentina |

## Marcas en los datos

- `fuente`: origen del dato (por ejemplo, `simulado`).
- `escenario_id`: identifica lo generado por una simulación en vivo, para poder borrarlo.

## Uso

*A completar:* cómo ejecutarlo como script y cómo importar sus funciones desde el dashboard.

Los datos son sintéticos y no representan fincas reales.
