"""Pantalla "Alertas" (ADR-020): qué alertas hubo en la noche, el historial de la temporada y las heladas por semana.

Solo presenta: todo lo que sale de MongoDB lo trae `data.py`. Las alertas "activas" son las de la noche elegida
(de las 18:00 a las 12:00), abiertas o cerradas: en la base todas cierran antes del mediodía.
"""

from html import escape

import pandas as pd
import streamlit as st

from dashboard import data
from dashboard.formato import noche_texto
from dashboard.lateral import barra_lateral
from dashboard.piezas_alertas import (TIPOS, filas_de_historial, filtrar, frase_de_alertas, tabla_de_la_noche,
                                      tabla_de_semanas)

finca_id = barra_lateral("paginas/alertas.py", con_finca=True)
fecha = st.session_state["fecha"]
r = data.alertas(fecha)

st.markdown(f'<h1 class="titulo">Alertas</h1>'
            f'<p class="subtitulo">{noche_texto(fecha)} · de 18:00 a 12:00, hora de Argentina</p>', unsafe_allow_html=True)

etiqueta = st.segmented_control("Tipo de alerta", list(TIPOS), default="Todas", required=True, key="tipo_alerta",
                                help="Filtra la lista de la noche y el historial. El resumen semanal es siempre de helada.")
tipo = TIPOS[etiqueta]
noche = filtrar(r["noche"], tipo, finca_id)
historial = filtrar(r["historial"], tipo, finca_id)

frase, detalle = frase_de_alertas(noche, None if tipo is None else etiqueta.lower())
st.markdown(f'<div class="estado" role="status"><div><div class="frase">{frase}</div>'
            f'<div class="detalle">{detalle}</div></div>'
            f'<div class="datos"><b>{len(historial)}</b> alerta{"s" if len(historial) != 1 else ""} en la temporada '
            f'hasta el {r["ahora"]:%d/%m/%Y}</div></div>', unsafe_allow_html=True)

st.markdown('<h2 class="seccion">Alertas de la noche</h2>', unsafe_allow_html=True)
if noche:
    st.markdown(tabla_de_la_noche(noche, fecha), unsafe_allow_html=True)
else:
    st.markdown('<div class="vacio">Sin alertas con este filtro en la noche elegida.</div>', unsafe_allow_html=True)

st.markdown('<h2 class="seccion" style="margin-top:2.2rem">Historial de la temporada</h2>', unsafe_allow_html=True)
if historial:
    tabla = pd.DataFrame(filas_de_historial(historial))
    st.dataframe(
        tabla, hide_index=True, height="auto",
        alt="Historial de alertas de la temporada hasta la fecha elegida, de la más reciente a la más antigua",
        column_config={
            "Inicio": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Fin": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Duración (h)": st.column_config.NumberColumn(format="%.1f h"),
        })
else:
    st.markdown('<div class="vacio">Todavía no hay alertas en la temporada con este filtro.</div>', unsafe_allow_html=True)

st.markdown('<h2 class="seccion" style="margin-top:2.2rem">Heladas por departamento y semana</h2>', unsafe_allow_html=True)
departamentos = r["departamentos"]
if finca_id is not None:
    de_la_finca = next(f["departamento"] for f in data.resumen(fecha)["catalogo"]["fincas"] if f["_id"] == finca_id)
    departamentos = [de_la_finca]
st.markdown(tabla_de_semanas(r["semanas"], departamentos), unsafe_allow_html=True)

with st.expander("Ver consulta"):
    st.caption("Las mismas consultas, escritas para mongosh (se pueden pegar en la consola o en Compass).")
    for titulo, texto in data.consultas_mongosh_alertas(fecha).items():
        st.markdown(f"**{escape(titulo)}**")
        st.code(texto, language="javascript")
