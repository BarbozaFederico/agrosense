# ADR-004: Temporada completa de Malbec, etapa fenológica e índice de riesgo

**Estado:** Aceptado (8/10/2026). Reemplaza la decisión 1 de [ADR-003](ADR-003-decisiones-modelado-inicial.md): `umbrales_fenologia` pasa a ser `variedades`.

## Contexto

El alcance original simulaba 30 días de septiembre sin una variedad definida. El equipo propuso seguir una variedad concreta a lo largo de la temporada, con su etapa fenológica, y estimar el daño por helada. Se evaluaron pros y contras de cada idea frente al plazo (entrega el 28/10/2026) y al foco de la materia (la base de datos).

## Decisiones

| Tema | Decisión |
|---|---|
| Variedad | **Malbec** en las 6 parcelas (la variedad con más datos de fuentes confiables en Mendoza) |
| Variedad simulada X | Opcional al final: un documento más en `variedades`, marcado como ficticio |
| Temporada simulada | **1/9/2026 a 31/3/2027** (212 días) |
| Frecuencia | 1 lectura cada 5 minutos por nodo: unas **732.700 lecturas** |
| Escala fenológica | Se guarda **BBCH** (numérica, permite consultas por rango); Baggiolini solo como equivalencia en el dashboard |
| Etapa fenológica | **Combinada:** estimación por grados-día (Q9) y observaciones manuales en `observaciones_fenologicas`; si hay observación, manda la observación |
| Riesgo de helada | **Índice de riesgo** (bajo, medio, alto) según horas bajo el umbral de la etapa, temperatura mínima, humedad del aire y humedad de suelo (Q10). No es un porcentaje de daño |
| Noches de helada | 6 a 8, entre septiembre y noviembre, en distintas etapas |
| Riego simulado | **Mixto:** turnos fijos más riegos extra cuando se abre la alerta de riego |
| Prioridad | Q9 y Q10 son parte del núcleo, al mismo nivel que Q1 a Q8 |

## Descartado

| Idea | Motivo |
|---|---|
| Variable de altura | No es claro qué altura se mediría (la del brote no la mide un sensor común) y no es el método estándar para estimar etapas; los grados-día salen de la temperatura ya medida |
| Daño en porcentaje por etapa BBCH | No hay curvas de daño con fuente verificada; inventarlas contradice la regla de no inventar datos. BBCH mide etapas, no daño. Queda como trabajo futuro |

## Alternativas de temporada

| Alternativa | Ventaja | Desventaja |
|---|---|---|
| Mantener 30 días sin variedad | Menos trabajo de simulador | Caso menos realista; menos volumen para medir índices |
| Temporada hasta diciembre | La mitad del simulador | No cubre verano ni riego intensivo |
| **Temporada completa (elegida)** | Ciclo completo, más volumen para índices, riego de verano | El simulador debe modelar toda la temporada |

## Consecuencias

- Nuevas colecciones: `variedades` (reemplaza a `umbrales_fenologia`) y `observaciones_fenologicas`.
- Nuevas consultas: Q9 (etapa estimada por grados-día, con `$setWindowFields` y suma acumulada) y Q10 (índice de riesgo por parcela y noche).
- Estimar la etapa no es pronóstico climático (que sigue fuera de alcance): usa datos ya medidos.
- **Dependen de la investigación profunda:** grados-día del Malbec por etapa, umbrales de helada por etapa BBCH, cortes del índice de riesgo, umbral de humedad de suelo y sistema de riego. Si no se consiguen los grados-día con fuente, Q9 se recorta y la etapa queda solo manual.
- Los pesos de la humedad del aire y del suelo en el índice de riesgo son supuestos, a validar.
- **Actualizado por [ADR-005](ADR-005-parametros-simulacion.md):** el índice usa margen más agravantes (no cuatro variables con el mismo peso), y se fijan los umbrales por etapa, el riego y el suelo de cada finca.

## Decisiones posteriores (8/10/2026)

| Tema | Decisión | Alternativas descartadas |
|---|---|---|
| Hora de referencia ("ahora") para Q5 y Q6 | **Selector de fecha en el dashboard:** las consultas reciben la fecha como parámetro y muestran la base como estaba ese día. Plan B si falta tiempo: fecha fija (31/3/2027 23:55) | Correr las fechas al cargar el seed (rompe el calendario de la temporada) |
| Observaciones fenológicas en la demo | **Solo precargadas en el seed** (por ejemplo, una por parcela por mes). El dashboard sigue siendo de solo lectura | Formulario en el dashboard (más trabajo de escritura y validación) |
