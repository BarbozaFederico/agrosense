# ADR-011: Umbrales de riego calculados con la FAO-56

**Estado:** Aceptado (19/10/2026). Reemplaza los umbrales de riego y de capacidad de campo de [ADR-005](ADR-005-parametros-simulacion.md) (decisión 5). Usa la FAO-56 (Allen et al. 1998), leída en el HTML oficial de fao.org.

## Contexto

El ADR-005 fijaba umbrales de humedad de suelo (franco 21 %, franco arenoso y pedregoso 13,5 % en septiembre y octubre) "adaptados de la FAO-56", pero la Tabla 19 no se había leído. Al leerla (capítulo 7, `x0490e0c.htm`) ninguna de esas cifras sale de ella: con p = 0,45 el franco da 19,2 %, no 21 %.

## Decisiones

| # | Tema | Elegida | Descartadas |
|---|---|---|---|
| 1 | Fórmula | `umbral = θFC − p × (θFC − θWP)` (FAO-56, ecuaciones 82 y 83) | — |
| 2 | Fracción `p` | **0,45 en los 4 períodos** (Tabla 22, vid de vino, verificada en el original) | `p` ajustado por ETc (0,60 / 0,55 / 0,47 / 0,54): depende de una ETo de tesis no verificada y de Kc y HRmin supuestos. `p` del ADR-005 (0,45 / 0,40 / 0,60 / 0,50): solo 0,45 tiene fuente FAO, y 0,60 es de riego deficitario |
| 3 | Valores de suelo | **Punto medio del rango** de la Tabla 19 para loam (franco) y sandy loam (franco arenoso) | Valores del Ejemplo 35 (sandy loam 0,23 / 0,10); medir cada parcela (no hay sensores reales) |
| 4 | Pedregoso | **Loamy sand con corrección por gravas, Rv = 0,30**: θFC y θWP × (1 − Rv) | Loamy sand sin corregir (11,2 %); franco arenoso (igualaba San Martín y Tupungato) |

## Resultado (% de humedad volumétrica)

| Suelo | Clase FAO | θFC / θWP usados | Umbral (los 4 períodos) |
|---|---|---|---|
| Franco | Loam | 0,25 / 0,12 | **19,2** |
| Franco arenoso | Sandy loam | 0,23 / 0,11 | **17,6** |
| Pedregoso | Loamy sand × (1 − 0,30) | 0,105 / 0,0455 | **7,8** |

La cuenta está en `db/seeds/umbrales_riego.py`. La estructura por período se mantiene en `configuracion.umbrales_riego` aunque hoy los 4 valores sean iguales, para poder ajustar `p` más adelante sin cambiar el esquema ni las consultas.

## Supuestos y límites (adoptados en ADR-012)

- **Rv = 0,30 es un valor inventado e ilustrativo.** Las gravas no retienen agua, así que reducen θFC y θWP del suelo completo; pero si el sensor midiera solo la tierra fina, el umbral a comparar sería 11,2 %. Elegir mal mueve el umbral unos 3 puntos.
- **Tratar la tierra fina del suelo pedregoso como loamy sand** se apoya en descripciones de bodegas (Zuccardi 2024), no en mediciones.
- **La textura pesa más que `p`:** dentro del rango de la Tabla 19, el franco con p = 0,45 va de 14,2 % a 24,2 %; entre períodos la diferencia sería de unos 2 puntos.
- **El punto medio no es una cifra de la FAO,** es un cálculo propio.
- Quedan sin verificar los datos locales del informe de investigación (ETo de una tesis y suelo de un solo viñedo de Las Compuertas); no se usan en los valores.
- El umbral de la FAO es el de **riego sin estrés**; no es el de riego deficitario controlado.

## Consecuencias

- `db/seeds/umbrales_riego.py` deja de ser `None`: el cargador ya puede cargar `configuracion`.
- Se corrigen `CLAUDE.md` y la decisión 5 del ADR-005, que mostraban los valores viejos. Las investigaciones de `docs/investigacion/` quedan como están (son el registro de lo que se encontró en su momento).
- Un umbral de 7,8 % en Tupungato implica que el simulador tiene que generar humedades de suelo realistas para un suelo pedregoso: es un dato de entrada para el diseño de las lecturas.
