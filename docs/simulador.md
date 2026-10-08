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
| Riego | Mixto: turnos fijos más riegos extra cuando se abre la alerta de riego. Sistema de riego: *a definir con investigación* |
| Fincas | San Rafael, Tupungato y San Martín (ficticias) |
| Etapas fenológicas | Escala BBCH; avance según grados-día del Malbec, *a definir con investigación* |

> **A resolver:** Q5 (últimos 30 minutos) y Q6 (últimas 24 horas) usan tiempos relativos, pero la temporada termina el 31/3/2027. Hay que definir una "hora de referencia" (por ejemplo, el fin de la historia) o ajustar las fechas al cargar el seed.

## Parámetros

*A completar:* semilla, rangos de temperatura, perfiles de descenso nocturno, ruido por nodo.

## Marcas en los datos

- `fuente`: origen del dato (por ejemplo, `simulado`).
- `escenario_id`: identifica lo generado por una simulación en vivo, para poder borrarlo.

## Uso

*A completar:* cómo ejecutarlo como script y cómo importar sus funciones desde el dashboard.

Los datos son sintéticos y no representan fincas reales.
