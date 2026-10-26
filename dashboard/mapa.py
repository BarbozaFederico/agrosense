"""Mapa de una finca: parcelas y nodos sin mapa base, polígonos en longitud y latitud (ADR-018).

Vive aparte de `app.py` para poder probarlo sin abrir Streamlit. El mapa es **fijo**: sin zoom, sin arrastre
y sin doble clic. Con los controles por defecto de Plotly, arrastrar el mouse sobre el dibujo hacía un zoom
que deformaba las parcelas y sacaba los nodos del cuadro (el rango de los ejes se recalculaba con la
proporción forzada por la latitud). Por eso el rango se calcula una vez, con margen, y se bloquea.
"""

import math
from html import escape

import plotly.graph_objects as go

from dashboard.estilo import COLORES

ESTADO_TEXTO = {"helada": "Helada", "atencion": "Atención", "normal": "Sin helada", "sin_umbral": "Sin umbral"}
RELLENO = {
    "helada": "rgba(255,122,107,.38)",
    "atencion": "rgba(240,184,74,.30)",
    "normal": "rgba(108,196,150,.18)",
    "sin_umbral": "rgba(140,143,149,.18)",
}
BORDE = {
    "helada": COLORES["helada"],
    "atencion": COLORES["atencion"],
    "normal": COLORES["normal"],
    "sin_umbral": COLORES["neutro"],
}
CONFIG = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False, "showTips": False}
MARGEN = 0.18  # espacio libre alrededor del dibujo, como fracción de su tamaño
ARRIBA_EXTRA = 0.25  # y un poco más arriba, para los rótulos de las parcelas
ALTO_PX = 250


def rango(valores: list[float], arriba: float = 0.0) -> list[float]:
    """Rango [mín, máx] de los ejes con margen. Si todos los valores son iguales abre un rango mínimo."""
    menor, mayor = min(valores), max(valores)
    ancho = (mayor - menor) or 1e-4
    return [menor - ancho * MARGEN, mayor + ancho * (MARGEN + arriba)]


def figura_finca(finca: dict, filas: list[dict], catalogo: dict, inactivos: set[str]) -> go.Figure:
    """Parcelas coloreadas por estado y nodos de una finca (hueco si el nodo no reporta)."""
    por_parcela = {f["parcela_id"]: f for f in filas}
    parcelas = [p for p in catalogo["parcelas"] if p["finca_id"] == finca["_id"]]
    nodos = [n for n in catalogo["nodos"] if n["finca_id"] == finca["_id"]]
    if not parcelas:
        raise ValueError(f"La finca {finca['_id']} no tiene parcelas para dibujar")
    fig = go.Figure()
    xs_todos, ys_todos = [], []
    for p in parcelas:
        anillo = p["geometria"]["coordinates"][0]
        xs, ys = [c[0] for c in anillo], [c[1] for c in anillo]
        xs_todos += xs
        ys_todos += ys
        f = por_parcela.get(p["_id"])
        estado = f["estado"] if f else "sin_umbral"
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                fill="toself",
                fillcolor=RELLENO[estado],
                line=dict(color=BORDE[estado], width=2),
                hoverinfo="text",
                text=f'{p["nombre"]}: {ESTADO_TEXTO[estado]}',
                showlegend=False,
                name=p["_id"],
            )
        )
        # nombre y estado en dos líneas: más angosto, no se pisa con el rótulo de la parcela vecina
        fig.add_annotation(
            x=sum(xs[:4]) / 4,
            y=max(ys),
            yshift=16,
            showarrow=False,
            text=f'<b>{escape(p["nombre"])}</b><br>{ESTADO_TEXTO[estado]}',
            font=dict(color=COLORES["tinta"], size=12),
        )
    for activo in (True, False):
        grupo = [n for n in nodos if (n["_id"] not in inactivos) == activo]
        if not grupo:
            continue
        x = [n["ubicacion"]["coordinates"][0] for n in grupo]
        y = [n["ubicacion"]["coordinates"][1] for n in grupo]
        xs_todos += x
        ys_todos += y
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                showlegend=False,
                hoverinfo="text",
                text=[n["_id"] for n in grupo],
                name="nodos que reportan" if activo else "nodos sin reportar",
                cliponaxis=False,
                marker=dict(
                    size=9,
                    color=COLORES["tinta"] if activo else "rgba(0,0,0,0)",
                    line=dict(color=COLORES["tinta"] if activo else COLORES["atencion"], width=2),
                ),
            )
        )
    lat0 = sum(ys_todos) / len(ys_todos)
    fig.update_layout(
        height=ALTO_PX,
        margin=dict(l=0, r=0, t=6, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode=False,
        hovermode="closest",
        xaxis=dict(visible=False, range=rango(xs_todos), fixedrange=True, constrain="domain"),
        yaxis=dict(
            visible=False,
            range=rango(ys_todos, ARRIBA_EXTRA),
            fixedrange=True,
            scaleanchor="x",
            scaleratio=1 / math.cos(math.radians(lat0)),
            constrain="domain",
        ),
        hoverlabel=dict(bgcolor=COLORES["panel"], font_color=COLORES["tinta"]),
    )
    return fig
