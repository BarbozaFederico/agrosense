# ADR-002: Interfaz con Streamlit

**Estado:** Aceptado.

## Contexto

El dashboard es parte obligatoria de la demo, corre en la notebook en local, es de escritorio y debe poder construirse en pocas semanas por un equipo de dos que está aprendiendo MongoDB.

## Decisión

Streamlit con Plotly, leyendo MongoDB con `pymongo`. Toda consulta vive en `dashboard/data.py`; `app.py` solo presenta.

## Alternativas evaluadas

| Opción | Resultado | Motivo |
|---|---|---|
| Streamlit | **Elegida** | Solo Python, la más rápida de armar, reutiliza el stack del simulador |
| Dash | Descartada | Exige callbacks y el diseño general requiere trabajo extra |
| Flask + Chart.js | Posible siguiente paso | Demo más pulida, pero implica plantillas, CSS y JavaScript |
| React o Svelte | Descartada | Agrega Node, empaquetado y dos proyectos; se aleja del foco de la materia |

## Consecuencias

- El diseño visual es más limitado; se compensa con tema oscuro y cuidado en los gráficos.
- Streamlit reejecuta el script en cada interacción: hay que cachear la conexión (`st.cache_resource`) y las consultas pesadas (`st.cache_data`).
- La simulación en vivo es delicada en este entorno y es lo primero que se recorta.
