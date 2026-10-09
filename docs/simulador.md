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
| Heladas | Mínimas en el sensor sin pasar los récords de septiembre (San Rafael −4,5 °C; San Martín −2,8 °C); la mínima ocurre al amanecer |
| Fincas | San Rafael, Tupungato y San Martín (ficticias) |
| Etapas fenológicas | Escala BBCH; grados-día base 10 °C desde el 1/9: 260 de brotación a floración y 712 de floración a envero (Zapata 2017); etapas intermedias repartidas en forma pareja (supuesto) |

> **Hora de referencia:** Q5 (últimos 30 minutos) y Q6 (últimas 24 horas) reciben la fecha "ahora" como parámetro, elegida con un selector en el dashboard (ADR-004). Las fechas del seed no se desplazan.

> **Observaciones fenológicas:** el seed incluye observaciones manuales precargadas (por ejemplo, una por parcela por mes).

## Parámetros

*A completar:* semilla, rangos de temperatura, perfiles de descenso nocturno, ruido por nodo.

## Marcas en los datos

- `fuente`: origen del dato (por ejemplo, `simulado`).
- `escenario_id`: identifica lo generado por una simulación en vivo, para poder borrarlo.

## Uso

*A completar:* cómo ejecutarlo como script y cómo importar sus funciones desde el dashboard.

Los datos son sintéticos y no representan fincas reales.
