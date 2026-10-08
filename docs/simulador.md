# Simulador

**Estado:** esqueleto, se completa en los Sprints A y B.

## Qué genera

- 30 días de lecturas para 12 nodos, 1 lectura cada 5 minutos (unas 103.680 lecturas).
- Escenarios normales y noches de helada distribuidos entre las 3 fincas y las semanas.
- Una noche de helada precargada para el dashboard (RF-13).

## Decisiones

| Tema | Valor |
|---|---|
| Período simulado | 1/9/2026 a 30/9/2026 (coincide con la brotación; no copia datos reales) |
| Noches de helada | 4, aproximadamente una por semana, repartidas entre las 3 fincas; una es la noche precargada |
| Fincas | San Rafael, Tupungato y San Martín (ficticias) |
| Estados fenológicos por parcela | *A definir con investigación*, buscando el caso más real posible |

> **A resolver:** Q5 (últimos 30 minutos) y Q6 (últimas 24 horas) usan tiempos relativos, pero la historia termina el 30/9. Hay que definir una "hora de referencia" (por ejemplo, el fin de la historia) o ajustar las fechas al cargar el seed.

## Parámetros

*A completar:* semilla, rangos de temperatura, perfiles de descenso nocturno, ruido por nodo.

## Marcas en los datos

- `fuente`: origen del dato (por ejemplo, `simulado`).
- `escenario_id`: identifica lo generado por una simulación en vivo, para poder borrarlo.

## Uso

*A completar:* cómo ejecutarlo como script y cómo importar sus funciones desde el dashboard.

Los datos son sintéticos y no representan fincas reales.
