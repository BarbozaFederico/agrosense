"""Textos y piezas HTML de la pantalla "Alertas" (ADR-020), sin Streamlit ni MongoDB.

Como `piezas.py`: cada función recibe lo que armó `data.py` y devuelve texto o HTML, así se prueban sin abrir el
dashboard. Todo lo que viene de la base pasa por `html.escape` antes de llegar al HTML.
"""

from datetime import date
from html import escape

from dashboard.formato import AGRAVANTES, TIPO_TEXTO, duracion, fecha_corta, grados, marca_tipo, numero
from dashboard.piezas import EJE_NOCHE, barra

TIPOS = {"Todas": None, "Helada": "helada", "Riego": "riego"}  # etiqueta del control -> tipo de alerta


def valor(a: dict, campo: str) -> str:
    """El valor de una alerta con su unidad: °C del brote en helada, % de humedad de suelo en riego (con 2 decimales:
    el valor extremo suele quedar a centésimas del umbral)."""
    return grados(a[campo]) if a["tipo"] == "helada" else f"{numero(a[campo], 2)} %"


def margen(a: dict) -> float:
    """Cuánto pasó el valor extremo del umbral (negativo = lo pasó). Sirve para ordenar de la más a la menos grave."""
    return a["valor_extremo"] - a["umbral"]


def ordenar_por_gravedad(filas: list[dict]) -> list[dict]:
    """Primero las de helada y, dentro de cada tipo, la que más pasó su umbral."""
    return sorted(filas, key=lambda a: (a["tipo"] != "helada", margen(a)))


def filtrar(filas: list[dict], tipo: str | None, finca_id: str | None) -> list[dict]:
    """Las alertas del tipo (None = todas) y de la finca (None = todas) elegidos."""
    return [a for a in filas if (tipo is None or a["tipo"] == tipo) and (finca_id is None or a["finca_id"] == finca_id)]


def frase_de_alertas(filas: list[dict], tipo: str | None = None) -> tuple[str, str]:
    """La respuesta en una frase (cuántas alertas hubo en la noche) y el detalle (la más fuerte). `tipo` es el filtro."""
    de = f" de {tipo}" if tipo else ""
    if not filas:
        return (
            f"No hubo alertas{de} esta noche.",
            "Las noches con alerta de helada están en la barra lateral." if tipo != "riego" else "",
        )
    n_h = sum(1 for a in filas if a["tipo"] == "helada")
    n_r = len(filas) - n_h
    partes = []
    if n_h:
        partes.append(f"{n_h} alerta{'s' if n_h > 1 else ''} de helada")
    if n_r:
        partes.append(f"{n_r} alerta{'s' if n_r > 1 else ''} de riego" if not n_h else f"{n_r} de riego")
    fincas = sorted({a["finca"] for a in filas})
    donde = f"en {fincas[0]} ({filas[0]['departamento']})" if len(fincas) == 1 else f"en {len(fincas)} fincas"
    frase = f"{' y '.join(partes)} esta noche, {donde}."
    fuerte = ordenar_por_gravedad(filas)[0]
    if fuerte["tipo"] == "helada":
        extra = f" Riesgo {fuerte['nivel']}." if fuerte["nivel"] else ""
        detalle = (
            f"La más fuerte: {fuerte['parcela']} de {fuerte['finca']}, {grados(fuerte['valor_extremo'])} en el brote "
            f"(umbral {grados(fuerte['umbral'])}), {duracion(fuerte['horas'])}.{extra}"
        )
    else:
        detalle = (
            f"La más baja: {fuerte['parcela']} de {fuerte['finca']} llegó a {valor(fuerte, 'valor_extremo')} de "
            f"humedad de suelo (umbral {valor(fuerte, 'umbral')})."
        )
    return frase, detalle


def tabla_de_la_noche(filas: list[dict], fecha: date) -> str:
    """Las alertas de la noche, con la barra de tiempo de 18:00 a 12:00 (la misma de "Resumen de la mañana")."""
    eje = "".join(f'<span style="left:{i * 16.667:.2f}%">{h}</span>' for i, h in enumerate(EJE_NOCHE))
    cab = (
        "<tr><th>Tipo</th><th>Parcela</th><th>Etapa</th><th class='num'>Valor extremo</th>"
        f"<th><div class='eje' aria-hidden='true'>{eje}</div></th><th class='num'>Duración</th><th>Riesgo</th></tr>"
    )
    cuerpo = []
    for a in ordenar_por_gravedad(filas):
        riesgo = "-"
        if a["nivel"]:
            det = ", ".join(AGRAVANTES[x] for x in a["agravantes"])
            riesgo = (
                f'<span class="chip {"helada" if a["nivel"] == "alto" else "atencion"}">{a["nivel"].capitalize()}</span>'
                + (f'<span class="sec">{det}</span>' if det else "")
            )
        cuerpo.append(
            f'<tr class="fila"><td>{marca_tipo(a["tipo"])}</td>'
            f'<td class="parcela"><a class="enlace" href="detalle?parcela={a["parcela_id"]}&fecha={fecha:%Y-%m-%d}" target="_self">'
            f'<b>{escape(a["parcela"])}</b></a><span class="sec">{escape(a["finca"])} · {escape(a["departamento"])}</span></td>'
            f'<td>{escape(a["etapa"])}</td>'
            f'<td class="num"><b>{valor(a, "valor_extremo")}</b><span class="sec">umbral {valor(a, "umbral")}</span></td>'
            f'<td>{barra(a, "" if a["tipo"] == "helada" else "riego")}</td>'
            f'<td class="num">{duracion(a["horas"])}{"+" if a["alerta"]["en_curso"] else ""}</td><td>{riesgo}</td></tr>'
        )
    return f'<div class="envoltorio"><table class="noche"><thead>{cab}</thead><tbody>{"".join(cuerpo)}</tbody></table></div>'


def filas_de_historial(historial: list[dict]) -> list[dict]:
    """El historial como filas de una tabla ordenable. El valor extremo y el umbral van como texto con su unidad
    (°C del brote o % de humedad): ordenar por un valor que mezcla unidades no tendría sentido."""
    return [
        {
            "Tipo": TIPO_TEXTO.get(a["tipo"], a["tipo"]),
            "Parcela": f"{a['parcela']} · {a['finca']}",
            "Etapa": a["etapa"],
            "Inicio": a["inicio"],
            "Fin": a["fin"],
            "Duración (h)": round(a["horas"], 2),
            "Valor extremo": valor(a, "valor_extremo"),
            "Umbral": valor(a, "umbral"),
            "Estado": "En curso" if a["fin"] is None else "Cerrada",
        }
        for a in historial
    ]


def tabla_de_semanas(semanas: list[dict], departamentos: list[str]) -> str:
    """Heladas por semana (filas) y departamento (columnas): cantidad de alertas y mínima del brote (Q8)."""
    if not semanas:
        return '<div class="vacio">Sin heladas registradas en la temporada.</div>'
    cab = "".join(f'<th class="num">{escape(d)}</th>' for d in departamentos)
    filas = []
    for s in semanas:
        celdas = []
        for d in departamentos:
            c = s["por_departamento"].get(d)
            celdas.append(
                '<td class="num">-</td>'
                if c is None
                else f'<td class="num"><b>{c["alertas"]}</b> alerta{"s" if c["alertas"] > 1 else ""}'
                f'<span class="sec">mín. {grados(c["minima_brote_c"])}</span></td>'
            )
        filas.append(
            f'<tr class="{"esta-noche" if s["actual"] else ""}"><td>Semana del {fecha_corta(s["semana"])}'
            f'{"<span class=sec> semana elegida</span>" if s["actual"] else ""}</td>{"".join(celdas)}</tr>'
        )
    return (
        f'<div class="envoltorio"><table class="q8"><thead><tr><th>Semana</th>{cab}</tr></thead>'
        f'<tbody>{"".join(filas)}</tbody></table></div>'
    )
