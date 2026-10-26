"""Pantalla "Detalle de parcela" (ADR-019): por qué saltó la alerta, y cómo estuvieron el suelo y el riego.

Solo presenta: todo lo que sale de MongoDB lo trae `data.py`. Se llega desde una fila de "Resumen de la mañana"
(el enlace lleva `?parcela=...&fecha=...`) o eligiendo la parcela en la barra lateral.
"""

from html import escape

import streamlit as st

from dashboard import data
from dashboard.formato import marca, noche_texto
from dashboard.graficos import figura_curva, figura_humedad
from dashboard.lateral import barra_lateral
from dashboard.mapa import CONFIG as CONFIG_GRAFICO
from dashboard.piezas import aviso_de_nodos, cifras, frase_de_la_parcela, semanas, tabla_de_riegos

# --------------------------------------------------------------------------- pantalla

parcela_id = barra_lateral("paginas/detalle.py", con_parcela=True)
fecha = st.session_state["fecha"]
d = data.detalle(fecha, parcela_id)

st.markdown(
    f'<h1 class="titulo">{escape(d["parcela"])} · {escape(d["finca"])}</h1>'
    f'<p class="subtitulo">{escape(d["departamento"])} · etapa {escape(d["etapa"])} · {noche_texto(fecha)}, '
    f"de 18:00 a 12:00, hora de Argentina</p>",
    unsafe_allow_html=True,
)
frase, detalle = frase_de_la_parcela(d)
st.markdown(
    f'<div class="estado" role="status"><div><div class="frase">{frase}</div>'
    f'<div class="detalle">{detalle}</div></div><div class="datos">{marca(d["estado"])}</div></div>',
    unsafe_allow_html=True,
)

st.markdown('<h2 class="seccion">La noche, minuto a minuto</h2>', unsafe_allow_html=True)
st.markdown(aviso_de_nodos(d), unsafe_allow_html=True)
if d["hay_curva"]:
    st.plotly_chart(figura_curva(d), width="stretch", config=CONFIG_GRAFICO, key="curva")
else:
    st.markdown('<div class="vacio">Sin lecturas de temperatura en esta noche.</div>', unsafe_allow_html=True)
st.markdown(cifras(d), unsafe_allow_html=True)

izquierda, derecha = st.columns([1, 1], gap="large")
with izquierda:
    st.markdown('<h2 class="seccion">Humedad de suelo, últimas 24 horas</h2>', unsafe_allow_html=True)
    if d["humedad"]:
        st.plotly_chart(figura_humedad(d), width="stretch", config=CONFIG_GRAFICO, key="humedad")
    else:
        st.markdown(
            '<div class="vacio">Sin lecturas de humedad de suelo en las últimas 24 horas.</div>', unsafe_allow_html=True
        )
with derecha:
    st.markdown('<h2 class="seccion">Riegos recientes</h2>', unsafe_allow_html=True)
    st.markdown(tabla_de_riegos(d) + semanas(d), unsafe_allow_html=True)

with st.expander("Ver consulta"):
    st.caption("Las mismas consultas, escritas para mongosh (se pueden pegar en la consola o en Compass).")
    for titulo, texto in data.consultas_mongosh_detalle(fecha, parcela_id).items():
        st.markdown(f"**{titulo}**")
        st.code(texto, language="javascript")
