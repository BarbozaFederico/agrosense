"""Pantalla "Estado de nodos" (ADR-021): qué sensores reportan, cuáles no y desde cuándo.

Solo presenta: todo lo que sale de MongoDB lo trae `data.py`. El "ahora" es el cierre de la noche elegida, las 12:00
de la mañana (igual que en las otras pantallas, ADR-018): un nodo no reporta si pasó más del límite desde su última lectura.
"""

from html import escape

import streamlit as st

from dashboard import data
from dashboard.formato import fecha_corta, hora
from dashboard.lateral import barra_lateral
from dashboard.piezas_nodos import filtrar, frase_de_nodos, tabla_de_nodos

finca_id = barra_lateral("paginas/nodos.py", con_finca=True)
fecha = st.session_state["fecha"]
r = data.nodos(fecha)
filas = filtrar(r["filas"], finca_id)

st.markdown(f'<h1 class="titulo">Estado de nodos</h1>'
            f'<p class="subtitulo">A las {hora(r["ahora"])} del {fecha_corta(r["ahora"])} de {r["ahora"]:%Y}, hora de Argentina '
            f'· sin reportar = más de {r["limite_min"]} minutos sin lecturas</p>', unsafe_allow_html=True)

frase, detalle = frase_de_nodos(filas, r["limite_min"])
ultima = r["ultima_de_la_red"]
datos = ("<span class=\"aviso\"><b>Sin lecturas</b> en la red</span>" if ultima is None
         else f'Último dato de la red: <b>{hora(ultima)}</b> del {fecha_corta(ultima)}')
st.markdown(f'<div class="estado" role="status"><div><div class="frase">{escape(frase)}</div>'
            f'<div class="detalle">{escape(detalle)}</div></div><div class="datos">{datos}</div></div>',
            unsafe_allow_html=True)

st.markdown('<h2 class="seccion">Los nodos, uno por uno</h2>', unsafe_allow_html=True)
if filas:
    st.markdown(tabla_de_nodos(filas, fecha), unsafe_allow_html=True)
else:
    st.markdown('<div class="vacio">No hay nodos para mostrar con este filtro.</div>', unsafe_allow_html=True)

with st.expander("Ver consulta"):
    st.caption("Las mismas consultas, escritas para mongosh (se pueden pegar en la consola o en Compass).")
    for titulo, texto in data.consultas_mongosh_nodos(fecha).items():
        st.markdown(f"**{escape(titulo)}**")
        st.code(texto, language="javascript")
