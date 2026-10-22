"""Textos y piezas HTML de las pantallas (ADR-018 y ADR-019), sin Streamlit ni MongoDB.

Cada función recibe lo que armó `data.py` y devuelve texto o HTML: así se prueban sin abrir el dashboard.
Todo lo que viene de la base pasa por `html.escape` antes de llegar al HTML.
"""

from datetime import date
from html import escape

from dashboard.formato import AGRAVANTES, duracion, fecha_corta, grados, hora, marca, numero

# --------------------------------------------------------------------------- Resumen de la mañana

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


def tabla(filas: list[dict], fecha: date) -> str:
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
            det = ", ".join(AGRAVANTES[x] for x in f["agravantes"])
            riesgo = f'<span class="chip {"helada" if f["nivel"] == "alto" else "atencion"}">{f["nivel"].capitalize()}</span>' + \
                     (f'<span class="sec">{det}</span>' if det else "")
        minima = ("-" if f["minima_brote_c"] is None else
                  f'<b>{grados(f["minima_brote_c"])}</b><span class="sec">umbral {grados(f["umbral_c"])}</span>')
        cuerpo.append(
            f'<tr class="fila"><td>{marca(f["estado"])}</td>'
            f'<td class="parcela"><a class="enlace" href="detalle?parcela={f["parcela_id"]}&fecha={fecha:%Y-%m-%d}" target="_self"><b>{escape(f["parcela"])}</b></a><span class="sec">{escape(f["finca"])} · {escape(f["departamento"])}</span></td>'
            f'<td>{escape(f["etapa"])}</td><td class="num">{minima}</td><td>{barra(f)}</td>'
            f'<td class="num">{horas}</td><td>{riesgo}</td><td>{texto_riego(f["riego"])}</td></tr>')
    return f'<div class="envoltorio"><table class="noche"><thead>{cab}</thead><tbody>{"".join(cuerpo)}</tbody></table></div>'



# --------------------------------------------------------------------------- Detalle de parcela

ORIGEN = {"turno": "Turno", "alerta": "Alerta de riego"}



def frase_de_la_parcela(d: dict) -> tuple[str, str]:
    """La respuesta en una frase (qué le pasó a la parcela) y el detalle (cuándo, cuánto y por qué riesgo)."""
    if not d["hay_curva"]:
        return "No hay lecturas de esta parcela en la noche elegida.", "Probá con otra fecha."
    a, regado = d["alerta"], d["riegos"] and d["riegos"][0]["inicio"] >= d["inicio"]
    if d["estado"] == "sin_umbral":
        return (f"En la etapa {d['etapa']} no hay umbral de helada: la parcela no se evalúa.",
                f"La curva muestra la temperatura igual; el sensor más frío llegó a {grados(d['minima_sensor_c'])}.")
    if d["estado"] == "helada":
        frase = f"{d['parcela']} bajó a {grados(d['minima_brote_c'])} en el brote, {numero(abs(d['margen_c']), 1)} °C bajo su umbral."
        partes = []
        if a:
            partes.append(f"Alerta de {hora(a['inicio'])} a {'la mañana (sigue abierta)' if a['fin'] is None else hora(a['fin'])}, "
                          f"{duracion(a['horas'])} bajo el umbral.")
        else:
            partes.append("No hay una alerta registrada para esta noche.")
        if d["nivel"]:
            extra = ", ".join(AGRAVANTES[x] for x in d["agravantes"])
            partes.append(f"Riesgo {d['nivel']}" + (f" ({extra})." if extra else "."))
        partes.append("Se regó durante la noche." if regado else "No se regó durante la noche.")
        return frase, " ".join(partes)
    if d["estado"] == "atencion":
        return (f"{d['parcela']} no bajó del umbral, pero quedó cerca: mínima de {grados(d['minima_brote_c'])} en el brote.",
                f"El umbral de {d['etapa']} es {grados(d['umbral_c'])}: margen de {numero(d['margen_c'], 1)} °C.")
    return (f"{d['parcela']} no bajó de su umbral: la mínima en el brote fue {grados(d['minima_brote_c'])}.",
            f"Quedó a {numero(d['margen_c'], 1)} °C del umbral de {d['etapa']} ({grados(d['umbral_c'])}).")


def cifras(d: dict) -> str:
    """Los números de la noche en una fila de texto, sin tarjetas."""
    def item(titulo: str, valor: str) -> str:
        return f"<div><dt>{titulo}</dt><dd>{valor}</dd></div>"
    horas = "-" if d["horas_bajo_cero"] is None else duracion(d["horas_bajo_cero"]) if d["horas_bajo_cero"] else "0 h"
    riesgo = "-"
    if d["nivel"] and d["estado"] in ("helada", "atencion"):
        riesgo = f'<span class="chip {"helada" if d["nivel"] == "alto" else "atencion"}">{d["nivel"].capitalize()}</span>'
    return ('<dl class="cifras">'
            + item("Mínima en el brote", grados(d["minima_brote_c"]))
            + item("Umbral de la etapa", grados(d["umbral_c"]))
            + item("Mínima del sensor", grados(d["minima_sensor_c"]))
            + item("Bajo 0 °C", horas)
            + item("Riesgo de helada", riesgo)
            + '</dl>')


def aviso_de_nodos(d: dict) -> str:
    """Un renglón si algún sensor de la parcela no reportó o está en mantenimiento."""
    avisos = []
    for n in d["nodos"]:
        if n["estado"] != "activo":
            avisos.append(f"{n['nodo_id']} está en {n['estado']}")
        elif n["lecturas"] == 0:
            avisos.append(f"{n['nodo_id']} no tiene lecturas en la noche")
    return f'<div class="aviso-nodos" role="status">{escape("; ".join(avisos))}.</div>' if avisos else ""


def tabla_de_riegos(d: dict) -> str:
    if not d["riegos"]:
        return '<div class="vacio">Sin riegos registrados hasta esta noche.</div>'
    filas = []
    for r in d["riegos"]:
        durante = r["inicio"] >= d["inicio"]
        filas.append(
            f'<tr class="{"esta-noche" if durante else ""}"><td>{fecha_corta(r["inicio"])}, {hora(r["inicio"])}'
            f'{"<span class=sec> esta noche</span>" if durante else ""}</td>'
            f'<td>{duracion((r["fin"] - r["inicio"]).total_seconds() / 3600)}</td>'
            f'<td class="num">{numero(r["lamina_mm"], 1)} mm</td><td class="num">{numero(r["litros"])} L</td>'
            f'<td>{ORIGEN.get(r["origen"], escape(r["origen"]))}</td></tr>')
    return ('<div class="envoltorio"><table class="riegos"><thead><tr><th>Inicio</th><th>Duración</th>'
            '<th class="num">Lámina</th><th class="num">Litros</th><th>Origen</th></tr></thead>'
            f'<tbody>{"".join(filas)}</tbody></table></div>')


def semanas(d: dict) -> str:
    if not d["semanas"]:
        return ""
    texto = " · ".join(f'semana del {fecha_corta(w["semana"])}: <b>{numero(w["litros"])} L</b>' for w in d["semanas"])
    return f'<div class="semanas">Últimas {len(d["semanas"])} semanas: {texto}</div>'
