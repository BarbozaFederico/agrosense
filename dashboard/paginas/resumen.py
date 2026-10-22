"""Pantalla "Resumen de la mañana" (ADR-018): qué se heló, cuánto bajó, desde cuándo y si ya se regó.

Solo presenta: todo lo que sale de MongoDB lo trae `data.py`.
"""

from html import escape

import streamlit as st

from dashboard import data
from dashboard.formato import hora, noche_texto
from dashboard.lateral import barra_lateral
from dashboard.mapa import CONFIG as CONFIG_MAPA, figura_finca
from dashboard.piezas import frase_de_estado, tabla

# --------------------------------------------------------------------------- pantalla

finca_id = barra_lateral(con_finca=True)
fecha = st.session_state["fecha"]
r = data.resumen(fecha)
filas = [f for f in r["filas"] if finca_id is None or f["finca_id"] == finca_id]
gravedad = {}                                    # las fincas con peor estado van primero
for f in r["filas"]:
    gravedad[f["finca_id"]] = min(gravedad.get(f["finca_id"], 9), data.ORDEN_ESTADO[f["estado"]])
fincas_visibles = sorted((f for f in r["catalogo"]["fincas"] if finca_id is None or f["_id"] == finca_id),
                         key=lambda f: (gravedad.get(f["_id"], 9), f["_id"]))
inactivos = {n["nodo_id"] for n in r["nodos_inactivos"]}

st.markdown(f'<h1 class="titulo">Resumen de la mañana</h1>'
            f'<p class="subtitulo">{noche_texto(fecha)} · de 18:00 a 12:00, hora de Argentina</p>', unsafe_allow_html=True)

frase, detalle = frase_de_estado(filas)
n_inact = len(inactivos)
if n_inact:
    nodos_txt = (f'<span class="aviso"><b>{n_inact} nodo{"s" if n_inact > 1 else ""} sin reportar</b></span>: '
                 f'{escape(", ".join(sorted(inactivos)))}')
else:
    nodos_txt = f'<b>{r["nodos_total"]} de {r["nodos_total"]}</b> nodos reportando'
if r["ultima_lectura"] is None:
    ultimo = '<span class="aviso"><b>Sin lecturas</b> en las últimas horas</span>'
else:
    atraso = "al cierre de la noche" if r["minutos_desde_ultima"] == 0 else f'{r["minutos_desde_ultima"]} min antes del cierre'
    ultimo = f'Último dato a las <b>{hora(r["ultima_lectura"])}</b> ({atraso})'
st.markdown(f'<div class="estado" role="status"><div><div class="frase">{frase}</div>'
            f'<div class="detalle">{detalle}</div></div><div class="datos">{nodos_txt}<br>{ultimo}</div></div>',
            unsafe_allow_html=True)

st.markdown('<h2 class="seccion">La noche, parcela por parcela</h2>', unsafe_allow_html=True)
if filas:
    st.markdown(tabla(filas, fecha), unsafe_allow_html=True)
else:
    st.markdown('<div class="vacio">No hay parcelas para mostrar con este filtro.</div>', unsafe_allow_html=True)

st.markdown('<h2 class="seccion" style="margin-top:2.2rem">Dónde está cada parcela</h2>'
            '<div class="leyenda"><span>Polígono: parcela, coloreada por estado</span>'
            '<span><i class="punto"></i>nodo que reporta</span><span><i class="punto hueco"></i>nodo sin reportar</span>'
            '<span>Sin mapa base: esquema de fincas ficticias</span></div>', unsafe_allow_html=True)
columnas = st.columns(len(fincas_visibles))
for col, finca in zip(columnas, fincas_visibles):
    with col:
        st.markdown(f'<div class="mapa-titulo">{escape(finca["nombre"])} · {escape(finca["departamento"])}</div>', unsafe_allow_html=True)
        st.plotly_chart(figura_finca(finca, filas, r["catalogo"], inactivos), width="stretch", config=CONFIG_MAPA,
                        key=f"mapa-{finca['_id']}")

with st.expander("Ver consulta"):
    st.caption("Las mismas consultas, escritas para mongosh (se pueden pegar en la consola o en Compass).")
    for titulo, texto in data.consultas_mongosh(fecha).items():
        st.markdown(f"**{titulo}**")
        st.code(texto, language="javascript")
