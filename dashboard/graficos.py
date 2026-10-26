"""Gráficos de "Detalle de parcela" (ADR-019): la curva de temperatura de la noche y la humedad de suelo.

Como el mapa (`mapa.py`), son **fijos**: sin zoom, sin arrastre y sin doble clic, con el rango de los ejes
calculado una vez. El detalle se lee con el cursor encima (una sola caja con todas las series de ese momento).
Sin Streamlit: reciben el diccionario que arma `data.armar_detalle` y devuelven una figura de Plotly.
"""

from datetime import timedelta

import plotly.graph_objects as go

from dashboard.estilo import COLORES
from dashboard.formato import grados, hora, numero

ALTO_CURVA_PX = 360
ALTO_HUMEDAD_PX = 240
SENSORES_RAYA = ["solid", "dot", "dash", "dashdot"]  # una raya distinta por sensor: no se distinguen solo por color


def _base(alto: int, rango_x: list, rango_y: list, ticks_x: tuple[list, list], sufijo_y: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=alto,
        margin=dict(l=8, r=28, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode=False,
        hovermode="x unified",
        font=dict(color=COLORES["tinta_2"], size=12),
        hoverlabel=dict(bgcolor=COLORES["panel"], font_color=COLORES["tinta"]),
        legend=dict(orientation="h", y=1.14, x=0, font=dict(color=COLORES["tinta_2"])),
        xaxis=dict(
            range=rango_x,
            fixedrange=True,
            hoverformat="%H:%M",
            tickvals=ticks_x[0],
            ticktext=ticks_x[1],
            showgrid=True,
            gridcolor=COLORES["costura"],
            zeroline=False,
            tickfont=dict(color=COLORES["tinta_2"]),
        ),
        yaxis=dict(
            range=rango_y,
            fixedrange=True,
            ticksuffix=sufijo_y,
            gridcolor=COLORES["costura"],
            zeroline=False,
            tickfont=dict(color=COLORES["tinta_2"]),
        ),
    )
    return fig


def figura_curva(d: dict) -> go.Figure:
    """Temperatura del brote (la que se compara con el umbral) y de los sensores, de las 18:00 a las 12:00."""
    inicio, fin = d["inicio"], d["ahora"]
    valores = [v for v in d["brote"]["y"] if v is not None] + [v for n in d["nodos"] for v in n["y"] if v is not None]
    if d["umbral_c"] is not None:
        valores.append(d["umbral_c"])
    bajo, alto = (min(valores), max(valores)) if valores else (-1.0, 1.0)
    margen = max(1.0, (alto - bajo) * 0.08)
    ticks = [inicio + timedelta(hours=3 * i) for i in range(7)]
    fig = _base(ALTO_CURVA_PX, [inicio, fin], [bajo - margen, alto + margen], (ticks, [hora(t) for t in ticks]), " °C")

    a = d["alerta"]
    if a is not None:
        fin_alerta = fin if a["fin"] is None else a["fin"]
        fig.add_vrect(x0=a["inicio"], x1=fin_alerta, fillcolor="rgba(255,122,107,.13)", line_width=0, layer="below")
    for i, n in enumerate(d["nodos"]):
        nombre = f"Sensor {n['nodo_id']}" + (" (en mantenimiento)" if n["estado"] == "mantenimiento" else "")
        fig.add_trace(
            go.Scatter(
                x=n["x"],
                y=n["y"],
                mode="lines",
                name=nombre,
                connectgaps=False,
                line=dict(color=COLORES["tinta_2"], width=1.2, dash=SENSORES_RAYA[i % len(SENSORES_RAYA)]),
                hovertemplate="%{y:.1f} °C",
            )
        )
    brote = d["brote"]
    fig.add_trace(
        go.Scatter(
            x=brote["x"],
            y=brote["y"],
            mode="lines",
            name="Brote (sensor más frío − 2 °C)",
            connectgaps=False,
            line=dict(color=COLORES["tinta"], width=3),
            hovertemplate="%{y:.1f} °C",
        )
    )
    if d["umbral_c"] is not None:
        # el tramo bajo el umbral se repinta en rojo; el estado también va en el texto, no solo en el color
        rojo = [y if (y is not None and y < d["umbral_c"]) else None for y in brote["y"]]
        if any(v is not None for v in rojo):
            fig.add_trace(
                go.Scatter(
                    x=brote["x"],
                    y=rojo,
                    mode="lines",
                    name="Bajo el umbral",
                    connectgaps=False,
                    line=dict(color=COLORES["helada"], width=3.5),
                    hoverinfo="skip",
                )
            )
        fig.add_hline(
            y=d["umbral_c"],
            line=dict(color=COLORES["atencion"], width=1.5, dash="dash"),
            annotation_text=f"Umbral ({d['etapa']}): {grados(d['umbral_c'])}",
            annotation_position="bottom left",
            annotation_font=dict(color=COLORES["atencion"], size=12),
        )
    if a is not None:
        fig.add_annotation(
            x=a["inicio"],
            y=1,
            yref="paper",
            xanchor="left",
            yanchor="top",
            showarrow=False,
            text=f"Alerta {hora(a['inicio'])} a {'la mañana' if a['fin'] is None else hora(a['fin'])}",
            font=dict(color=COLORES["helada"], size=12),
        )
    return fig


def figura_humedad(d: dict) -> go.Figure:
    """Humedad de suelo promedio por hora de las últimas 24 horas (Q6), con el umbral de riego de ese suelo."""
    horas = d["humedad"]
    inicio, fin = d["ahora"] - timedelta(hours=24), d["ahora"]
    pcts = [h["pct"] for h in horas] + [d["umbral_riego_pct"]]
    bajo, alto = min(pcts), max(pcts)
    margen = max(1.0, (alto - bajo) * 0.15)
    ticks = [inicio + timedelta(hours=6 * i) for i in range(5)]
    fig = _base(ALTO_HUMEDAD_PX, [inicio, fin], [bajo - margen, alto + margen], (ticks, [hora(t) for t in ticks]), " %")
    fig.update_layout(showlegend=False)
    if horas:
        fig.add_trace(
            go.Scatter(
                x=[h["hora"] for h in horas],
                y=[h["pct"] for h in horas],
                mode="lines+markers",
                name="Humedad de suelo",
                line=dict(color=COLORES["tinta"], width=2.5),
                marker=dict(size=5, color=COLORES["tinta"]),
                hovertemplate="%{y:.1f} %",
            )
        )
    fig.add_hline(
        y=d["umbral_riego_pct"],
        line=dict(color=COLORES["atencion"], width=1.5, dash="dash"),
        annotation_text=f"Umbral de riego: {numero(d['umbral_riego_pct'], 1)} %",
        annotation_position="bottom left",
        annotation_font=dict(color=COLORES["atencion"], size=12),
    )
    return fig
