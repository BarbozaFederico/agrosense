# ADR-005: Parámetros de helada, riego y suelo

**Estado:** Aceptado (8/10/2026). Completa [ADR-004](ADR-004-temporada-malbec.md) con los datos de [`investigacion/verificacion-fuentes.md`](../investigacion/verificacion-fuentes.md), [`vid-malbec.md`](../investigacion/vid-malbec.md) y [`vid-malbec-complemento.md`](../investigacion/vid-malbec-complemento.md).

## Contexto

Las investigaciones dejaron cuatro decisiones de diseño abiertas: cómo calcular el índice de riesgo, qué riego tiene cada finca, qué suelo tiene cada parcela y si la alerta usa la temperatura del sensor o la del brote. Además, los umbrales de helada de los documentos eran de **frutales** (IDR + DACC) y había que reemplazarlos por valores de vid.

## Decisiones

### 1. Temperatura del brote

La alerta compara el umbral con la **temperatura estimada en el brote**, no con la del sensor:

`T_brote = T_sensor − Δ`

| Elegida | Alternativa descartada |
|---|---|
| **Temperatura estimada en el brote.** En noches calmas el brote está 1 a 3 °C más frío que el abrigo (Trought et al. 1999; FAO 2005). Más realista | Temperatura del sensor: más simple, pero subestima el riesgo |

- La lectura del sensor se guarda tal cual; Δ es un parámetro de configuración.
- El proyecto no mide viento ni nubosidad, así que **Δ = 2 °C fijo** (supuesto, a validar). Es configurable.

### 2. Índice de riesgo de helada (Q10): margen más agravantes

| Elegida | Alternativa descartada |
|---|---|
| **Margen más agravantes.** La FAO indica que la mínima pesa más que la duración | Cuatro variables con el mismo peso: contradice la evidencia |

Margen = mínima de `T_brote` en la noche − umbral de la etapa.

| Paso | Regla |
|---|---|
| Nivel base | **Bajo** si el margen es > 2 °C; **medio** si está entre 0 y 2 °C; **alto** si es ≤ 0 °C |
| Duración | Sube un nivel si `T_brote` pasa 2 h o más por debajo de umbral + 1 °C |
| Aire seco (helada negra) | Sube un nivel si la humedad del aire nocturna es < 60 % |
| Suelo seco | Sube un nivel (solo de bajo a medio) si la humedad de suelo está bajo el umbral de riego |
| Tope | Nunca supera "alto". No es un porcentaje de daño |

Los cortes son **adaptados** de la FAO y de las dos investigaciones; se defienden como diseño propio.

### 3. Umbral de helada por etapa (colección `variedades`, Malbec)

| BBCH | Cómo se ve la planta | Umbral (`T_brote`) | Fuente | Marca |
|---|---|---|---|---|
| 00 | Yema dormida | −10,6 °C | WSU EB1615 (Concord, primera hinchazón) | con fuente |
| 01-05 | Yema hinchada o algodonosa | −6,1 °C | WSU EB1615 (Concord) | con fuente |
| 07-09 | Brotación: punta verde | −3,9 °C | WSU EB1615; FDF 2016 da −2 a −4 °C | con fuente |
| 11 | Primera hoja | −2,8 °C | WSU EB1615 | con fuente |
| 12-15 | 2 a 5 hojas | −2,2 °C | WSU EB1615 | con fuente |
| 53-57 | Racimos visibles | −1,2 °C | Ferguson et al. 2014 (Malbec, tejido verde) | adaptado |
| 60-71 | Floración y cuaje | 0 °C | FDF / INIA 2016 | con fuente |

Los valores de WSU son temperaturas de 10 % de daño, medidas en laboratorio en uva Concord (más resistente que la vinífera). Se reemplazan los valores de frutales del IDR + DACC.

### 4. Riego por finca

| Finca | Sistema | Volumen y frecuencia | Marca |
|---|---|---|---|
| San Rafael | Surco por turno | 76 mm brutos por riego, cada 7 días; riego extra si salta la alerta | con fuente (Morábito; turnos DGI) |
| San Martín | Surco por turno | Igual que San Rafael | con fuente |
| Tupungato | Goteo | ~1,5 mm/día en octubre, ~3,5 mm/día de diciembre a febrero; extra si salta la alerta | adaptado (De Lorenzi; FAO-56) |

| Elegida | Alternativas descartadas |
|---|---|
| **Surco en San Rafael y San Martín, goteo en Tupungato.** El 90 % de Mendoza riega por superficie; los viñedos de altura del Valle de Uco usan goteo. Q7 compara dos sistemas | Goteo en las tres (menos realista); surco en las tres (sin contraste) |

### 5. Suelo por finca

| Finca | Suelo | Capacidad de campo | Umbral de riego (sept-oct) | Marca |
|---|---|---|---|---|
| San Rafael | Franco | ~28 % | ~21 % | supuesto (sin fuente de suelos para San Rafael) |
| San Martín | Franco arenoso | ~18 % (aprox.) | ~13,5 % | adaptado (descripción de la zona Este) |
| Tupungato | Pedregoso | ~18 % | ~13,5 % | adaptado (Zuccardi 2024) |

| Elegida | Alternativas descartadas |
|---|---|
| **Un suelo por finca** | Un suelo por parcela (más supuestos); franco en todas (menos realista) |

El umbral de riego cambia por período según la fracción "p" (`vid-malbec.md`, valores recomendados "d"). Los valores de capacidad de campo son generales por textura y deben confirmarse con la Tabla 19 de la FAO-56.

## Consecuencias

- `variedades` guarda, por etapa BBCH, el umbral de helada y los grados-día; la configuración guarda Δ y los cortes del índice.
- `fincas` o `parcelas` guardan el sistema de riego y el tipo de suelo; el umbral de riego se obtiene del suelo y del período.
- La humedad del aire nocturna y la humedad de suelo entran al índice de riesgo como agravantes, junto con la duración.
- Se corrigen `CLAUDE.md` y `requisitos.md`, que todavía mostraban los umbrales de frutales.
- Siguen como supuestos: Δ = 2 °C, la densidad de plantación (4.000 plantas/ha) y la capacidad de campo por textura.
