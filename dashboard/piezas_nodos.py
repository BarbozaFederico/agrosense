"""Textos y piezas HTML de la pantalla "Estado de nodos" (ADR-021), sin Streamlit ni MongoDB.

Como `piezas.py`: cada función recibe lo que armó `data.py` y devuelve texto o HTML, así se prueban sin abrir el
dashboard. Todo lo que viene de la base pasa por `html.escape` antes de llegar al HTML.
"""

from datetime import date
from html import escape

from dashboard.formato import duracion_larga, fecha_corta, hora, marca_reporte

ESTADO_ADMINISTRATIVO = {"activo": "Activo", "mantenimiento": "Mantenimiento", "baja": "Baja"}


def filtrar(filas: list[dict], finca_id: str | None) -> list[dict]:
    """Los nodos de la finca elegida (None = todas)."""
    return [n for n in filas if finca_id is None or n["finca_id"] == finca_id]


def hace(n: dict) -> str:
    """Cuánto pasó desde el último reporte, escrito para leer rápido."""
    if n["minutos"] is None:
        return "-"
    return "al cierre" if n["minutos"] == 0 else duracion_larga(n["minutos"])


def frase_de_nodos(filas: list[dict], limite_min: int) -> tuple[str, str]:
    """La respuesta en una frase (cuántos nodos reportan) y el detalle (cuáles no y desde cuándo)."""
    if not filas:
        return "No hay nodos para mostrar.", ""
    sin = [n for n in filas if not n["reporta"]]
    if not sin:
        return (f"Los {len(filas)} nodos reportan.",
                f"Un nodo se marca como sin reportar cuando pasan más de {limite_min} minutos sin lecturas.")
    nombres = ", ".join(n["nodo_id"] for n in sin)
    frase = (f"{len(sin)} de {len(filas)} nodos sin reportar: {nombres}." if len(sin) > 1
             else f"1 de {len(filas)} nodos sin reportar: {nombres}.")
    peor = sin[0]
    desde = "no tiene ninguna lectura" if peor["minutos"] is None else f"lleva {duracion_larga(peor['minutos'])} sin datos"
    detalle = f"{peor['nodo_id']} ({peor['parcela']} de {peor['finca']}) {desde}"
    if peor["ultima"] is not None:
        detalle += f"; su último reporte fue el {fecha_corta(peor['ultima'])} a las {hora(peor['ultima'])}"
    return frase, detalle + "."


def _estado_del_nodo(n: dict) -> str:
    """El estado administrativo del catálogo, con una aclaración cuando contradice al reporte real."""
    chip = {"activo": "", "mantenimiento": "atencion", "baja": "neutro"}.get(n["estado_nodo"], "neutro")
    texto = escape(ESTADO_ADMINISTRATIVO.get(n["estado_nodo"], n["estado_nodo"]))
    base = f'<span class="chip {chip}">{texto}</span>' if chip else texto
    if n["estado_nodo"] != "activo" and n["reporta"]:
        return base + '<span class="sec">sigue reportando</span>'
    if n["estado_nodo"] == "activo" and not n["reporta"]:
        return base + '<span class="sec">activo, pero no reporta</span>'
    return base


def tabla_de_nodos(filas: list[dict], fecha: date) -> str:
    """Una fila por nodo; los que no reportan van resaltados."""
    cab = ("<tr><th>Reporte</th><th>Nodo</th><th>Parcela</th><th>Último reporte</th><th class='num'>Hace</th>"
           "<th>Estado del nodo</th></tr>")
    cuerpo = []
    for n in filas:
        ultimo = ("Sin lecturas" if n["ultima"] is None else f'{fecha_corta(n["ultima"])}, {hora(n["ultima"])}')
        cuerpo.append(
            f'<tr class="fila{"" if n["reporta"] else " sin-reporte"}"><td>{marca_reporte(n["reporta"])}</td>'
            f'<td><b>{escape(n["nodo_id"])}</b></td>'
            f'<td class="parcela"><a class="enlace" href="detalle?parcela={n["parcela_id"]}&fecha={fecha:%Y-%m-%d}" target="_self">'
            f'<b>{escape(n["parcela"])}</b></a><span class="sec">{escape(n["finca"])} · {escape(n["departamento"])}</span></td>'
            f'<td>{ultimo}</td><td class="num">{hace(n)}</td><td>{_estado_del_nodo(n)}</td></tr>')
    return f'<div class="envoltorio"><table class="noche"><thead>{cab}</thead><tbody>{"".join(cuerpo)}</tbody></table></div>'
