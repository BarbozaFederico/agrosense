"""agrosense - dashboard (ADR-002 y ADR-018). Primera pantalla: "Resumen de la mañana".

Solo presenta: todo lo que sale de MongoDB lo trae `data.py`.
Se corre desde la raíz del repo:  streamlit run dashboard/app.py
"""

import math
import sys
from datetime import date
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # para importar `db` y `dashboard` desde la raíz

from dashboard import data                      # noqa: E402
from dashboard.estilo import COLORES, CSS       # noqa: E402

FECHA_INICIAL = date(2026, 10, 5)               # la noche de helada precargada (RF-13)
TEMPORADA = (date(2026, 9, 1), date(2027, 3, 31))
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
ESTADO_TEXTO = {"helada": "Helada", "atencion": "Atención", "normal": "Sin helada", "sin_umbral": "Sin umbral"}
ESTADO_FORMA = {   # una forma distinta por estado, para no depender solo del color
    "helada": '<path d="M7 1 13 7 7 13 1 7Z" fill="currentColor"/>',
    "atencion": '<path d="M7 1.5 13 12.5H1Z" fill="currentColor"/>',
    "normal": '<circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="2"/>',
    "sin_umbral": '<path d="M2 7h10" stroke="currentColor" stroke-width="2"/>',
}


# --------------------------------------------------------------------------- formato

def grados(v: float | None) -> str:
    return "-" if v is None else f"{v:.1f}".replace("-", "−").replace(".", ",") + " °C"


def duracion(horas: float) -> str:
    minutos = round(horas * 60)
    return f"{minutos // 60} h {minutos % 60:02d} min" if minutos >= 60 else f"{minutos} min"


def hora(d) -> str:
    return f"{d:%H:%M}"


def fecha_larga(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def noche_texto(d: date) -> str:
    previo = date.fromordinal(d.toordinal() - 1)
    if previo.month == d.month:
        return f"Noche del {previo.day} al {d.day} de {MESES[d.month - 1]} de {d.year}"
    return f"Noche del {previo.day} de {MESES[previo.month - 1]} al {d.day} de {MESES[d.month - 1]} de {d.year}"


def marca(estado: str) -> str:
    return (f'<span class="marca-estado {estado}"><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">'
            f'{ESTADO_FORMA[estado]}</svg>{ESTADO_TEXTO[estado]}</span>')


# --------------------------------------------------------------------------- piezas

def frase_de_estado(filas: list[dict]) -> tuple[str, str]:
    """La respuesta en una frase (qué se heló) y el detalle (la peor parcela y si se regó)."""
    evaluadas = [f for f in filas if f["estado"] != "sin_umbral"]
    heladas = [f for f in filas if f["estado"] == "helada"]
    atencion = [f for f in filas if f["estado"] == "atencion"]
    sin_umbral = len(filas) - len(evaluadas)
    nota = f" {sin_umbral} sin umbral en su etapa: no se evalúan." if sin_umbral else ""
    if heladas:
        peor = heladas[0]
        regadas = sum(1 for f in heladas if f["riego"]["estado"] == "esta_noche")
        riego = ("Ninguna se regó durante la noche." if regadas == 0 else
                 f"{regadas} de {len(heladas)} se regaron durante la noche.")
        n = len(heladas)
        frase = f"{n} de {len(evaluadas)} parcelas bajaron de su umbral de helada."
        detalle = (f"La peor: {peor['parcela']} de {peor['finca']}, con {grados(peor['minima_brote_c'])} en el brote "
                   f"contra un umbral de {grados(peor['umbral_c'])}. {riego}{nota}")
        return frase, detalle
    if atencion:
        frase = f"Ninguna parcela bajó de su umbral, pero {len(atencion)} quedó{'' if len(atencion) == 1 else 'aron'} cerca."
        a = atencion[0]
        return frase, f"{a['parcela']} de {a['finca']} llegó a {grados(a['minima_brote_c'])} en el brote (umbral {grados(a['umbral_c'])}).{nota}"
    if not evaluadas:
        return "Ninguna parcela tiene umbral de helada en su etapa.", nota.strip()
    return "Ninguna parcela bajó de su umbral esta noche.", f"Todas quedaron a más de 2 °C del umbral.{nota}"


def texto_riego(r: dict) -> str:
    if r["estado"] == "esta_noche":
        return f'<b>Regó a las {hora(r["inicio"])}</b><span class="sec">{r["lamina_mm"]:g} mm</span>'.replace(".", ",")
    if r["estado"] == "antes":
        cuando = "hoy" if r["hace_dias"] == 0 else ("hace 1 día" if r["hace_dias"] == 1 else f"hace {r['hace_dias']} días")
        return f'Sin regar<span class="sec">Último riego {cuando}</span>'
    return 'Sin regar<span class="sec">Sin riegos registrados</span>'


def barra(f: dict) -> str:
    """La noche de 18:00 a 12:00; en rojo, lo que duró la alerta de helada."""
    a = f["alerta"]
    marcas = "".join(f'<i style="left:{p:.2f}%"></i>' for p in (16.67, 33.33, 50, 66.67, 83.33))
    if a is None:
        cuerpo = '<em>sin alerta registrada</em>' if f["estado"] == "helada" else ""
    else:
        ancho = max(0.8, (a["hasta"] - a["desde"]) * 100)
        cuerpo = (f'<b class="{"abierta" if a["en_curso"] else ""}" style="left:{a["desde"] * 100:.2f}%;width:{ancho:.2f}%"></b>')
    rotulo = "" if a is None else f"Alerta de {hora(a['inicio'])} a {'la mañana' if a['fin'] is None else hora(a['fin'])}"
    return f'<div class="barra" role="img" aria-label="{escape(rotulo or "Sin alerta en la noche")}">{marcas}{cuerpo}</div>'


def tabla(filas: list[dict]) -> str:
    eje = "".join(f'<span style="left:{i * 16.667:.2f}%">{h}</span>' for i, h in enumerate(["18", "21", "00", "03", "06", "09", "12"]))
    cab = ("<tr><th>Estado</th><th>Parcela</th><th>Etapa</th><th class='num'>Mínima en el brote</th>"
           f"<th><div class='eje' aria-hidden='true'>{eje}</div></th><th class='num'>Bajo el umbral</th>"
           "<th>Riesgo</th><th>Riego</th></tr>")
    cuerpo = []
    for f in filas:
        a = f["alerta"]
        horas = "-" if a is None else duracion(a["horas"]) + ("" if not a["en_curso"] else "+")
        riesgo = "-"
        if f["nivel"] and f["estado"] in ("helada", "atencion"):
            extras = {"duracion": "larga duración", "aire_seco": "aire seco", "suelo_seco": "suelo seco"}
            det = ", ".join(extras[x] for x in f["agravantes"])
            riesgo = f'<span class="chip {"helada" if f["nivel"] == "alto" else "atencion"}">{f["nivel"].capitalize()}</span>' + \
                     (f'<span class="sec">{det}</span>' if det else "")
        minima = ("-" if f["minima_brote_c"] is None else
                  f'<b>{grados(f["minima_brote_c"])}</b><span class="sec">umbral {grados(f["umbral_c"])}</span>')
        cuerpo.append(
            f'<tr class="fila"><td>{marca(f["estado"])}</td>'
            f'<td class="parcela"><b>{escape(f["parcela"])}</b><span class="sec">{escape(f["finca"])} · {escape(f["departamento"])}</span></td>'
            f'<td>{escape(f["etapa"])}</td><td class="num">{minima}</td><td>{barra(f)}</td>'
            f'<td class="num">{horas}</td><td>{riesgo}</td><td>{texto_riego(f["riego"])}</td></tr>')
    return f'<div class="envoltorio"><table class="noche"><thead>{cab}</thead><tbody>{"".join(cuerpo)}</tbody></table></div>'


def mapa(finca: dict, filas: list[dict], catalogo: dict, inactivos: set[str]) -> go.Figure:
    """Parcelas y nodos de una finca, sin mapa base: polígonos en longitud y latitud."""
    relleno = {"helada": "rgba(255,122,107,.38)", "atencion": "rgba(240,184,74,.30)",
               "normal": "rgba(108,196,150,.18)", "sin_umbral": "rgba(140,143,149,.18)"}
    borde = {"helada": COLORES["helada"], "atencion": COLORES["atencion"],
             "normal": COLORES["normal"], "sin_umbral": COLORES["neutro"]}
    por_parcela = {f["parcela_id"]: f for f in filas}
    fig = go.Figure()
    lats = []
    for p in (p for p in catalogo["parcelas"] if p["finca_id"] == finca["_id"]):
        anillo = p["geometria"]["coordinates"][0]
        xs, ys = [c[0] for c in anillo], [c[1] for c in anillo]
        lats += ys
        f = por_parcela.get(p["_id"])
        estado = f["estado"] if f else "sin_umbral"
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", fill="toself", fillcolor=relleno[estado], line=dict(color=borde[estado], width=2),
            hoverinfo="text", text=f'{p["nombre"]}: {ESTADO_TEXTO[estado]}', showlegend=False))
        fig.add_annotation(x=sum(xs[:4]) / 4, y=max(ys), yshift=12, showarrow=False,
                           text=f'<b>{escape(p["nombre"])}</b> · {ESTADO_TEXTO[estado]}',
                           font=dict(color=COLORES["tinta"], size=12))
    nodos = [n for n in catalogo["nodos"] if n["finca_id"] == finca["_id"]]
    for activo in (True, False):
        grupo = [n for n in nodos if (n["_id"] not in inactivos) == activo]
        if grupo:
            fig.add_trace(go.Scatter(
                x=[n["ubicacion"]["coordinates"][0] for n in grupo], y=[n["ubicacion"]["coordinates"][1] for n in grupo],
                mode="markers", showlegend=False, hoverinfo="text", text=[n["_id"] for n in grupo],
                marker=dict(size=9, color=COLORES["tinta"] if activo else "rgba(0,0,0,0)",
                            line=dict(color=COLORES["tinta"] if activo else COLORES["atencion"], width=2))))
    lat0 = sum(lats) / len(lats)
    fig.update_layout(
        height=250, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, constrain="domain"),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1 / math.cos(math.radians(lat0))),
        hoverlabel=dict(bgcolor=COLORES["panel"], font_color=COLORES["tinta"]))
    return fig


# --------------------------------------------------------------------------- pantalla

st.set_page_config(page_title="agrosense · Resumen de la mañana", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

if "fecha" not in st.session_state:
    st.session_state["fecha"] = FECHA_INICIAL


def ir_a(dia: date) -> None:
    st.session_state["fecha"] = dia


with st.sidebar:
    st.markdown('<div class="marca">agrosense <span>· viñedos</span></div>'
                '<ul class="nav"><li class="activa">Resumen de la mañana</li>'
                '<li>Detalle de parcela<small>en construcción</small></li>'
                '<li>Alertas<small>en construcción</small></li>'
                '<li>Estado de nodos<small>en construcción</small></li></ul>', unsafe_allow_html=True)
    catalogo_fincas = data.resumen(st.session_state["fecha"])["catalogo"]["fincas"]
    nombres = {f["_id"]: f"{f['nombre']} · {f['departamento']}" for f in catalogo_fincas}
    finca_id = st.selectbox("Finca", [None, *nombres], format_func=lambda k: "Todas las fincas" if k is None else nombres[k])
    st.date_input("Mañana de la noche", min_value=TEMPORADA[0], max_value=TEMPORADA[1], key="fecha", format="DD/MM/YYYY",
                  help="Define la noche que se muestra: de las 18:00 del día anterior a las 12:00 de esta fecha.")
    heladas = data.noches_con_helada()
    st.caption("Noches con alerta de helada")
    for i, dia in enumerate(heladas):
        st.button(f"{dia.day} de {MESES[dia.month - 1][:3]}", key=f"noche{i}", on_click=ir_a, args=(dia,),
                  type="primary" if dia == st.session_state["fecha"] else "secondary", width="stretch")
    st.markdown('<span class="etiqueta-sim">datos simulados</span>', unsafe_allow_html=True)

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
    st.markdown(tabla(filas), unsafe_allow_html=True)
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
        st.plotly_chart(mapa(finca, filas, r["catalogo"], inactivos), width="stretch", config={"displayModeBar": False},
                        key=f"mapa-{finca['_id']}")

with st.expander("Ver consulta"):
    st.caption("Las mismas consultas, escritas para mongosh (se pueden pegar en la consola o en Compass).")
    for titulo, texto in data.consultas_mongosh(fecha).items():
        st.markdown(f"**{titulo}**")
        st.code(texto, language="javascript")
