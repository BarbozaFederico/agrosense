# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Streamlit + Plotly + pymongo (confirmado el 21/10/2026: se mantiene ADR-002). Dashboard web de escritorio, local, sin internet. Todo el repo es Python; las consultas viven en `db/queries/` y `dashboard/data.py` las llama y cachea.

## Users

Usuario que manda en el diseño: el productor o encargado de finca que abre el panel a la mañana temprano (hora de Argentina) después de una noche fría. Pregunta: qué parcelas se helaron, desde cuándo, cuánto bajó y si ya se regó. Secundarios: técnico agrónomo (horas bajo el umbral, etapa BBCH, índice de riesgo) y administrador del sistema (nodos caídos, backup). Evaluador de la cátedra: ve la demo en una notebook; la evaluación es individual.

## Product Purpose

agrosense es un proyecto de Diseño de Bases de Datos II (Universidad de Mendoza, 2026, entrega 28/10/2026) que monitorea sensores en viñedos (temperatura, humedad de suelo y de aire) sobre MongoDB, con alertas de helada y de riego. El dashboard muestra la capa de datos funcionando; no resuelve el problema real del viñatero porque los datos son simulados.

## Positioning

El riesgo de helada se mide por parcela y se compara con el umbral de la etapa fenológica del Malbec en esa fecha (temperatura estimada en el brote = sensor − 2 °C), no con un único valor para todo el oasis.

## Operating Context

Demo en notebook, de escritorio, tema oscuro, sin internet (mapa sin mapa base, polígonos en Plotly). Hora de Argentina (UTC−3); una noche va de las 18:00 a las 12:00. Selector de fecha de referencia ("ahora" de las consultas) y selector de finca. Noche de helada precargada (San Rafael, 5/10/2026, 03:00 a 08:00, mínima −6,3 °C en el sensor).

## Capabilities and Constraints

- 3 fincas ficticias (San Rafael, San Martín, Tupungato), 6 parcelas (2 por finca), 12 nodos, Malbec. Temporada simulada 1/9/2026 a 31/3/2027, 727.980 lecturas.
- 4 pantallas obligatorias: resumen de finca, detalle de parcela, alertas, estado de nodos. Cada una con panel "Ver consulta" y etiqueta visible "datos simulados".
- Alertas: helada (umbral por etapa BBCH) y riego (umbral de humedad de suelo por tipo de suelo). Una alerta por evento, se cierra sola; el índice de riesgo (bajo, medio, alto) se guarda al cerrar.
- Nodo inactivo: sin lecturas hace más de 30 min. Indicador "último dato hace X min".
- Lenguaje del productor: parcela, helada, riego; nunca documento ni colección.
- Fuera de alcance: móvil, pronóstico, alerta temprana, mapa base, edición de datos (el dashboard es de solo lectura).
- Opcional (se recorta primero): simulación de la noche en vivo.
- Idioma de la UI: español rioplatense. Repo público: sin credenciales.

## Evidence on Hand

Datos reales del seed y del simulador en MongoDB local; Q1 a Q10 implementadas en `db/queries/`. No hay wireframes, maquetas ni código de UI (`dashboard/` está vacío).

## Product Principles

1. La primera vista responde "qué se heló y qué hay que hacer" antes que cualquier otra cosa.
2. Cada alerta dice qué parcela, qué temperatura, desde cuándo y si ya se regó.
3. Confianza en el dato: la frescura y los nodos caídos son visibles, no se esconden.
4. Funciona sin internet y se entiende sin saber qué es una base de datos.
5. Semáforo consistente (normal, atención, helada) legible en oscuro y sin depender solo del color.

## Accessibility & Inclusion

Contraste verificado sobre fondo oscuro; estado nunca solo por color.
