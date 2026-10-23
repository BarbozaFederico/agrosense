"""Datos del dashboard (ADR-002 y ADR-014): llama a las consultas de `db/queries` y las cachea.

`app.py` solo presenta; todo lo que sale de MongoDB pasa por acá. La función `armar_resumen` no
toca la base ni Streamlit (recibe los resultados de las consultas), así se puede probar sola.
Las fechas llegan de las consultas en UTC y acá se pasan a hora de Argentina (UTC-3).
"""

from datetime import date, datetime, timedelta

import streamlit as st

from db.conexion import obtener_base
from db.queries import (alertas_pantalla as ap, comun, detalle_parcela as dp, estado_nodos as en, q1_horas_bajo_cero as q1, q5_nodos_sin_reportar as q5,
                        q6_humedad_suelo_horaria as q6, q7_litros_por_semana as q7, q8_heladas_por_departamento as q8,
                        q9_etapa_por_grados_dia as q9,
                        q10_riesgo_de_helada as q10, resumen_manana as rm)

VENTANA_H = 18                      # la noche: de las 18:00 a las 12:00
CORTE_MAX_MIN = 10                  # más de 10 minutos sin lectura (un nodo reporta cada 5) corta la línea de la curva
SEMANAS_DE_RIEGO = 4                # semanas que se resumen en el panel de riegos
CORTES_POR_DEFECTO = {"margen_alto_c": 0, "margen_bajo_c": 2}      # los de `configuracion.riesgo` (ADR-005)
ORDEN_ESTADO = {"helada": 0, "atencion": 1, "normal": 2, "sin_umbral": 3}


@st.cache_resource
def base():
    """Una sola conexión para toda la sesión (pymongo ya maneja su propio pool)."""
    return obtener_base()


# --------------------------------------------------------------------------- armado (puro)

def _local(valor: datetime) -> datetime:
    return comun.a_hora_local(valor)


def _fraccion(momento: datetime, inicio: datetime) -> float:
    """Posición (0 a 1) de un momento dentro de la noche."""
    horas = (comun.a_utc(momento) - inicio).total_seconds() / 3600
    return min(1.0, max(0.0, horas / VENTANA_H))


def _estado(margen: float, cortes: dict) -> str:
    if margen <= cortes["margen_alto_c"]:
        return "helada"
    return "atencion" if margen <= cortes["margen_bajo_c"] else "normal"


def _alerta(alerta: dict | None, inicio: datetime, fin: datetime) -> dict | None:
    if alerta is None:
        return None
    a_ini = comun.a_utc(alerta["inicio"])
    a_fin = comun.a_utc(alerta["fin"]) if alerta["fin"] else fin
    a_ini_vis, a_fin_vis = max(a_ini, inicio), min(a_fin, fin)
    return {"inicio": _local(a_ini), "fin": None if alerta["fin"] is None else _local(a_fin),
            "en_curso": alerta["fin"] is None or a_fin >= fin,
            "horas": max(0.0, (a_fin_vis - a_ini_vis).total_seconds() / 3600),
            "desde": _fraccion(a_ini, inicio), "hasta": _fraccion(a_fin, inicio)}


def _riego(riego: dict | None, inicio: datetime, ahora: datetime) -> dict:
    """¿Se regó durante la noche? Si no, hace cuánto fue el último riego."""
    if riego is None:
        return {"estado": "nunca"}
    r_ini = comun.a_utc(riego["inicio"])
    if r_ini >= inicio:
        return {"estado": "esta_noche", "inicio": _local(r_ini), "lamina_mm": riego["lamina_mm"]}
    return {"estado": "antes", "hace_dias": (ahora - r_ini).days, "lamina_mm": riego["lamina_mm"],
            "inicio": _local(r_ini)}


def armar_resumen(fecha: date, riesgo: list[dict], etapas: dict[str, dict], alertas: list[dict],
                  riegos: dict[str, dict], inactivos: list[dict], ultima: datetime | None, catalogo: dict,
                  config: dict) -> dict:
    """Junta los resultados de las consultas en lo que muestra la pantalla.

    `etapas` es el resultado de q9.etapas_estimadas. Una parcela cuya etapa no tiene umbral de helada
    (por ejemplo, "Hojas desplegadas") no aparece en Q10: se muestra como "sin_umbral" y no se evalúa."""
    inicio, ahora = comun.ventana_noche(fecha)
    fincas = {f["_id"]: f for f in catalogo["fincas"]}
    parcelas = {p["_id"]: p for p in catalogo["parcelas"]}
    alerta_de = {}
    for a in alertas:                       # una parcela podría tener 2 alertas en la noche: vale la más extrema
        previa = alerta_de.get(a["parcela_id"])
        if previa is None or a["valor_extremo"] < previa["valor_extremo"]:
            alerta_de[a["parcela_id"]] = a

    filas = []
    for r in riesgo:
        p = parcelas[r["parcela_id"]]
        f = fincas[p["finca_id"]]
        filas.append({
            "parcela_id": r["parcela_id"], "parcela": p["nombre"], "finca_id": f["_id"], "finca": f["nombre"],
            "departamento": f["departamento"], "etapa": r["etapa"], "umbral_c": r["umbral_helada_c"],
            "minima_brote_c": r["minima_brote_c"], "margen_c": r["margen_c"],
            "estado": _estado(r["margen_c"], config["riesgo"]), "nivel": r["nivel"], "agravantes": r["agravantes"],
            "alerta": _alerta(alerta_de.get(r["parcela_id"]), inicio, ahora),
            "riego": _riego(riegos.get(r["parcela_id"]), inicio, ahora)})
    for pid, e in etapas.items():
        if pid in {f["parcela_id"] for f in filas}:
            continue
        p = parcelas[pid]
        f = fincas[p["finca_id"]]
        filas.append({
            "parcela_id": pid, "parcela": p["nombre"], "finca_id": f["_id"], "finca": f["nombre"],
            "departamento": f["departamento"], "etapa": e["etapa"], "umbral_c": None, "minima_brote_c": None,
            "margen_c": 99.0, "estado": "sin_umbral", "nivel": None, "agravantes": [],
            "alerta": _alerta(alerta_de.get(pid), inicio, ahora), "riego": _riego(riegos.get(pid), inicio, ahora)})
    filas.sort(key=lambda x: (ORDEN_ESTADO[x["estado"]], x["margen_c"]))

    nodos_total = len(catalogo["nodos"])
    return {
        "fecha": fecha, "inicio": _local(inicio), "ahora": _local(ahora),
        "filas": filas, "catalogo": catalogo,
        "nodos_total": nodos_total, "nodos_inactivos": inactivos,
        "ultima_lectura": None if ultima is None else _local(ultima),
        "minutos_desde_ultima": None if ultima is None else int((ahora - ultima).total_seconds() // 60),
    }


# --------------------------------------------------------------------------- detalle de parcela (puro)

def con_cortes(puntos: list[tuple[datetime, float]], max_min: int = CORTE_MAX_MIN) -> tuple[list, list]:
    """(x, y) de una serie, con un hueco (None) donde faltan más de `max_min` minutos de lecturas:
    Plotly no une los dos lados de un hueco, así un corte de reporte se ve como corte y no como una recta."""
    xs, ys = [], []
    for i, (t, v) in enumerate(puntos):
        if i and (t - puntos[i - 1][0]).total_seconds() > max_min * 60:
            xs.append(t)
            ys.append(None)
        xs.append(t)
        ys.append(v)
    return xs, ys


def armar_detalle(fecha: date, parcela_id: str, catalogo: dict, riesgo: dict | None, etapa: dict,
                  horas_bajo_cero: dict | None, curva: list[dict], humedad: list[dict], riegos: list[dict],
                  semanas: list[dict], alertas: list[dict], umbral_riego: float, delta_c: float) -> dict:
    """Junta los resultados de las consultas en lo que muestra "Detalle de parcela".

    `riesgo` es la fila de Q10 de la parcela (None si su etapa no tiene umbral); `etapa`, la de q9.etapas_estimadas;
    `horas_bajo_cero`, la de Q1. La temperatura del brote es la del nodo más frío en cada instante menos `delta_c`."""
    inicio, ahora = comun.ventana_noche(fecha)
    parcela = next(p for p in catalogo["parcelas"] if p["_id"] == parcela_id)
    finca = next(f for f in catalogo["fincas"] if f["_id"] == parcela["finca_id"])
    nodos_catalogo = {n["_id"]: n for n in catalogo["nodos"] if n["parcela_id"] == parcela_id}

    por_nodo: dict[str, list] = {}
    mas_frio: dict[datetime, float] = {}
    for fila in curva:
        t = _local(fila["ts"])
        por_nodo.setdefault(fila["nodo_id"], []).append((t, fila["temperatura_c"]))
        mas_frio[t] = min(fila["temperatura_c"], mas_frio.get(t, float("inf")))
    nodos = []
    for nid in sorted(nodos_catalogo):
        puntos = por_nodo.get(nid, [])
        x, y = con_cortes(puntos)
        nodos.append({"nodo_id": nid, "estado": nodos_catalogo[nid]["estado"], "lecturas": len(puntos), "x": x, "y": y})
    brote_x, brote_y = con_cortes([(t, round(v - delta_c, 2)) for t, v in sorted(mas_frio.items())])

    alerta = min(alertas, key=lambda a: a["valor_extremo"]) if alertas else None
    return {
        "fecha": fecha, "parcela_id": parcela_id, "parcela": parcela["nombre"], "finca": finca["nombre"],
        "departamento": finca["departamento"], "etapa": etapa["etapa"],
        "umbral_c": None if riesgo is None else riesgo["umbral_helada_c"],
        "estado": "sin_umbral" if riesgo is None else _estado(riesgo["margen_c"], CORTES_POR_DEFECTO),
        "minima_brote_c": None if riesgo is None else riesgo["minima_brote_c"],
        "margen_c": None if riesgo is None else riesgo["margen_c"],
        "nivel": None if riesgo is None else riesgo["nivel"],
        "agravantes": [] if riesgo is None else riesgo["agravantes"],
        "horas_bajo_cero": None if horas_bajo_cero is None else horas_bajo_cero["horas_bajo_cero"],
        "minima_sensor_c": None if horas_bajo_cero is None else horas_bajo_cero["minima_c"],
        "alerta": _alerta(alerta, inicio, ahora), "inicio": _local(inicio), "ahora": _local(ahora),
        "nodos": nodos, "brote": {"x": brote_x, "y": brote_y}, "hay_curva": bool(curva),
        "humedad": [{"hora": _local(h["hora"]), "pct": h["humedad_suelo_pct"]} for h in humedad],
        "umbral_riego_pct": umbral_riego,
        "riegos": [{"inicio": _local(r["inicio"]), "fin": _local(r["fin"]), "lamina_mm": r["lamina_mm"],
                    "litros": r["litros"], "origen": r["origen"], "sistema": r["sistema"]} for r in riegos],
        "semanas": [{"semana": _local(w["semana"]), "litros": w["litros"], "riegos": w["riegos"]} for w in semanas],
    }


# --------------------------------------------------------------------------- alertas (puro)

def nombre_de_etapa(bbch: int, etapas: list[dict]) -> str:
    """Nombre de la etapa a la que pertenece un número BBCH (las alertas guardan solo el número)."""
    for e in etapas:
        if e["bbch_desde"] <= bbch <= e["bbch_hasta"]:
            return e["nombre"]
    return f"BBCH {bbch}"


def _fila_de_alerta(a: dict, parcelas: dict, fincas: dict, etapas: list[dict], inicio: datetime, ahora: datetime) -> dict:
    p = parcelas[a["parcela_id"]]
    f = fincas[p["finca_id"]]
    a_ini = comun.a_utc(a["inicio"])
    a_fin = comun.a_utc(a["fin"]) if a["fin"] else None
    return {
        "tipo": a["tipo"], "parcela_id": a["parcela_id"], "parcela": p["nombre"], "finca_id": f["_id"],
        "finca": f["nombre"], "departamento": f["departamento"], "etapa": nombre_de_etapa(a["etapa_bbch"], etapas),
        "umbral": a["umbral"], "valor_extremo": a["valor_extremo"],
        "nivel": (a.get("riesgo") or {}).get("nivel"), "agravantes": (a.get("riesgo") or {}).get("agravantes", []),
        "inicio": _local(a_ini), "fin": None if a_fin is None else _local(a_fin),
        "horas": ((a_fin or ahora) - a_ini).total_seconds() / 3600,
        "alerta": _alerta(a, inicio, ahora),
    }


def armar_alertas(fecha: date, noche: list[dict], historial: list[dict], semanas: list[dict], catalogo: dict,
                  etapas: list[dict]) -> dict:
    """Junta los resultados de las consultas en lo que muestra "Alertas".

    `noche` y `historial` son alertas de ambos tipos; `semanas`, el resultado de Q8 (solo helada); `etapas`, las de la
    variedad. `alerta` de cada fila de la noche tiene la posición de su barra de tiempo (como en "Resumen de la mañana")."""
    inicio, ahora = comun.ventana_noche(fecha)
    fincas = {f["_id"]: f for f in catalogo["fincas"]}
    parcelas = {p["_id"]: p for p in catalogo["parcelas"]}
    departamentos = sorted({f["departamento"] for f in catalogo["fincas"]})
    lunes = _local(comun.medianoche_local(fecha - timedelta(days=fecha.weekday())))
    por_semana: dict[datetime, dict] = {}
    for s in semanas:
        por_semana.setdefault(_local(s["semana"]), {})[s["departamento"]] = {
            "alertas": s["alertas"], "parcelas": s["parcelas_afectadas"], "minima_brote_c": s["minima_brote_c"]}
    return {
        "fecha": fecha, "inicio": _local(inicio), "ahora": _local(ahora), "departamentos": departamentos,
        "noche": [_fila_de_alerta(a, parcelas, fincas, etapas, inicio, ahora) for a in noche],
        "historial": [_fila_de_alerta(a, parcelas, fincas, etapas, inicio, ahora) for a in historial],
        "semanas": [{"semana": s, "por_departamento": por_semana[s], "actual": s == lunes} for s in sorted(por_semana)],
    }


# --------------------------------------------------------------------------- estado de nodos (puro)

def armar_nodos(fecha: date, nodos: list[dict], catalogo: dict, limite_min: int) -> dict:
    """Junta el último reporte de cada nodo en lo que muestra "Estado de nodos".

    `nodos` es el resultado de `estado_nodos.ultimo_reporte`; `limite_min`, `configuracion.nodo_inactivo_min`.
    Un nodo no reporta si pasó más del límite desde su última lectura o si no tiene ninguna (igual que Q5).
    Los que no reportan van primero (el de más tiempo arriba) y después el resto por nombre."""
    _, ahora = comun.ventana_noche(fecha)
    parcelas = {p["_id"]: p for p in catalogo["parcelas"]}
    fincas = {f["_id"]: f for f in catalogo["fincas"]}
    filas = []
    for n in nodos:
        minutos = n["minutos_sin_reportar"]
        p = parcelas[n["parcela_id"]]
        f = fincas[n["finca_id"]]
        filas.append({
            "nodo_id": n["nodo_id"], "parcela_id": n["parcela_id"], "parcela": p["nombre"], "finca_id": f["_id"],
            "finca": f["nombre"], "departamento": f["departamento"], "estado_nodo": n["estado"],
            "ultima": None if n["ultima_lectura"] is None else _local(n["ultima_lectura"]),
            "minutos": minutos, "reporta": minutos is not None and minutos <= limite_min})
    # sin reportar primero (sin lecturas, luego el de más tiempo); los que reportan, por nombre
    filas.sort(key=lambda x: (x["reporta"], 0 if x["reporta"] else -(float("inf") if x["minutos"] is None else x["minutos"]),
                              x["nodo_id"]))
    ultimas = [f["ultima"] for f in filas if f["ultima"] is not None]
    return {"fecha": fecha, "ahora": _local(ahora), "limite_min": limite_min, "filas": filas,
            "ultima_de_la_red": max(ultimas) if ultimas else None}


# --------------------------------------------------------------------------- con caché

@st.cache_data(show_spinner="Consultando la base…")
def resumen(fecha: date) -> dict:
    """Todo lo que necesita 'Resumen de la mañana' para la noche que termina en la mañana `fecha`."""
    bd = base()
    config = comun.configuracion(bd)
    ahora = rm.ahora_de_la_noche(fecha)
    return armar_resumen(
        fecha, q10.consultar(bd, fecha), q9.etapas_estimadas(bd, fecha), rm.alertas_de_helada(bd, fecha), rm.ultimo_riego(bd, fecha),
        q5.consultar(bd, ahora), rm.ultima_lectura(bd, ahora), rm.catalogo(bd), config)


@st.cache_data(show_spinner="Consultando la base…")
def detalle(fecha: date, parcela_id: str) -> dict:
    """Todo lo que necesita "Detalle de parcela" para una parcela y la noche que termina en la mañana `fecha`."""
    bd = base()
    config = comun.configuracion(bd)
    ahora = dp.cierre_de_la_noche(fecha)
    riesgo = next((r for r in q10.consultar(bd, fecha) if r["parcela_id"] == parcela_id), None)
    h0 = next(iter(q1.consultar(bd, fecha, parcela_id)), None)
    return armar_detalle(
        fecha, parcela_id, rm.catalogo(bd), riesgo, q9.etapas_estimadas(bd, fecha)[parcela_id], h0,
        dp.curva_de_la_noche(bd, fecha, parcela_id), q6.consultar(bd, ahora, parcela_id),
        dp.riegos_recientes(bd, fecha, parcela_id),
        q7.consultar(bd, parcela_id, ahora - timedelta(weeks=SEMANAS_DE_RIEGO), ahora),
        [a for a in rm.alertas_de_helada(bd, fecha) if a["parcela_id"] == parcela_id],
        q10.umbral_de_riego_por_parcela(bd, fecha)[parcela_id], config["delta_brote_c"])


@st.cache_data
def consultas_mongosh_detalle(fecha: date, parcela_id: str) -> dict[str, str]:
    """El texto de mongosh de cada consulta que alimenta "Detalle de parcela" (panel 'Ver consulta')."""
    bd = base()
    ahora = dp.cierre_de_la_noche(fecha)
    desde = ahora - timedelta(weeks=SEMANAS_DE_RIEGO)
    return {
        "Curva de temperatura de la noche": comun.texto_mongosh("lecturas", dp.pipeline_curva_de_la_noche(fecha, parcela_id)),
        "Horas bajo 0 °C (Q1)": comun.texto_mongosh("lecturas", q1.pipeline(fecha, parcela_id)),
        "Humedad de suelo por hora (Q6)": comun.texto_mongosh("lecturas", q6.pipeline(ahora, parcela_id)),
        "Riegos recientes": comun.texto_mongosh("riegos", dp.pipeline_riegos_recientes(fecha, parcela_id)),
        "Litros por semana (Q7)": comun.texto_mongosh("riegos", q7.pipeline(parcela_id, desde, ahora)),
        "Alertas de helada de la noche": comun.texto_mongosh("alertas", rm.pipeline_alertas_de_helada(fecha)),
        "Riesgo de helada (Q10)": comun.texto_mongosh("lecturas", q10.pipeline(
            fecha, q9.etapas_estimadas(bd, fecha), q10.umbral_de_riego_por_parcela(bd, fecha), comun.configuracion(bd))),
    }


@st.cache_data(show_spinner="Consultando la base…")
def alertas(fecha: date) -> dict:
    """Todo lo que necesita "Alertas" para la noche que termina en la mañana `fecha`."""
    bd = base()
    return armar_alertas(fecha, ap.alertas_de_la_noche(bd, fecha), ap.historial(bd, fecha), q8.consultar(bd),
                         rm.catalogo(bd), ap.etapas_del_malbec(bd))


@st.cache_data
def consultas_mongosh_alertas(fecha: date) -> dict[str, str]:
    """El texto de mongosh de cada consulta que alimenta "Alertas" (panel 'Ver consulta')."""
    return {
        "Alertas de la noche": comun.texto_mongosh("alertas", ap.pipeline_alertas_de_la_noche(fecha)),
        "Historial de la temporada": comun.texto_mongosh("alertas", ap.pipeline_historial(fecha)),
        "Heladas por departamento y semana (Q8)": comun.texto_mongosh("alertas", q8.pipeline()),
    }


@st.cache_data(show_spinner="Consultando la base…")
def nodos(fecha: date) -> dict:
    """Todo lo que necesita "Estado de nodos": el último reporte de cada nodo hasta las 12:00 de la mañana `fecha`."""
    bd = base()
    ahora = dp.cierre_de_la_noche(fecha)
    return armar_nodos(fecha, en.ultimo_reporte(bd, ahora), rm.catalogo(bd), comun.configuracion(bd)["nodo_inactivo_min"])


@st.cache_data
def consultas_mongosh_nodos(fecha: date) -> dict[str, str]:
    """El texto de mongosh de cada consulta que alimenta "Estado de nodos" (panel 'Ver consulta')."""
    bd = base()
    ahora = dp.cierre_de_la_noche(fecha)
    return {
        "Último reporte de cada nodo": comun.texto_mongosh("nodos", en.pipeline_ultimo_reporte(ahora)),
        "Nodos sin reportar (Q5)": comun.texto_mongosh("nodos", q5.pipeline(ahora, comun.configuracion(bd)["nodo_inactivo_min"])),
    }


@st.cache_data
def noches_con_helada() -> list[date]:
    return rm.noches_con_helada(base())


@st.cache_data
def consultas_mongosh(fecha: date) -> dict[str, str]:
    """El texto de mongosh de cada consulta que alimenta la pantalla (panel 'Ver consulta')."""
    bd = base()
    config = comun.configuracion(bd)
    ahora = rm.ahora_de_la_noche(fecha)
    return {
        "Riesgo de helada por parcela (Q10)": comun.texto_mongosh("lecturas", q10.pipeline(
            fecha, q9.etapas_estimadas(bd, fecha), q10.umbral_de_riego_por_parcela(bd, fecha), config)),
        "Alertas de helada de la noche": comun.texto_mongosh("alertas", rm.pipeline_alertas_de_helada(fecha)),
        "Último riego de cada parcela": comun.texto_mongosh("riegos", rm.pipeline_ultimo_riego(fecha)),
        "Nodos sin reportar (Q5)": comun.texto_mongosh("nodos", q5.pipeline(ahora, config["nodo_inactivo_min"])),
    }
