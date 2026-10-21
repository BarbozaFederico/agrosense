"""Datos del dashboard (ADR-002 y ADR-014): llama a las consultas de `db/queries` y las cachea.

`app.py` solo presenta; todo lo que sale de MongoDB pasa por acá. La función `armar_resumen` no
toca la base ni Streamlit (recibe los resultados de las consultas), así se puede probar sola.
Las fechas llegan de las consultas en UTC y acá se pasan a hora de Argentina (UTC-3).
"""

from datetime import date, datetime, timedelta

import streamlit as st

from db.conexion import obtener_base
from db.queries import (comun, q5_nodos_sin_reportar as q5, q9_etapa_por_grados_dia as q9,
                        q10_riesgo_de_helada as q10, resumen_manana as rm)

VENTANA_H = 18                      # la noche: de las 18:00 a las 12:00
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
