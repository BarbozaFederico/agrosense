"""Consultas de apoyo de la pantalla "Resumen de la mañana" del dashboard (ADR-018).

No son parte de Q1 a Q10: completan lo que esa pantalla necesita y ninguna de ellas toca los datos.
Tienen la misma forma que las demás (`pipeline_xxx` y `consultar_xxx`):
    alertas_de_helada   alertas de helada que se solapan con la noche (barra de tiempo de la tabla)
    ultimo_riego        último riego de cada parcela hasta el fin de la noche ("¿ya se regó?")
    ultima_lectura      momento de la última lectura de la base hasta un "ahora" (frescura del dato)
    noches_con_helada   mañanas con al menos una alerta de helada (atajos del selector de fecha)

Una noche va de las 18:00 del día anterior a las 12:00 de la mañana elegida, hora de Argentina (ADR-014).
"""

from datetime import date, datetime, timedelta

from db.queries import comun

FRESCURA_MAX_H = 6      # cuánto hacia atrás se busca la última lectura (acota el barrido)


def ahora_de_la_noche(fecha: date) -> datetime:
    """El "ahora" de la pantalla: el cierre de la noche (12:00 hora de Argentina), como UTC con zona."""
    return comun.ventana_noche(fecha)[1]


# --------------------------------------------------------------------------- alertas

def pipeline_alertas_de_helada(fecha: date) -> list:
    """Alertas de helada que empezaron antes del cierre de la noche y no terminaron antes de su comienzo."""
    inicio, fin = comun.ventana_noche(fecha)
    return [
        {"$match": {"tipo": "helada", "inicio": {"$lt": fin},
                    "$or": [{"fin": None}, {"fin": {"$gte": inicio}}]}},
        {"$project": {"_id": 0, "parcela_id": 1, "inicio": 1, "fin": 1, "estado": 1, "etapa_bbch": 1,
                      "umbral": 1, "valor_extremo": 1, "riesgo": 1}},
        {"$sort": {"inicio": 1}},
    ]


def alertas_de_helada(bd, fecha: date | str = comun.FECHA_NOCHE) -> list[dict]:
    return list(bd.alertas.aggregate(pipeline_alertas_de_helada(comun.a_fecha(fecha))))


# --------------------------------------------------------------------------- riego

def pipeline_ultimo_riego(fecha: date) -> list:
    """Para cada parcela, su riego más reciente que haya empezado antes del cierre de la noche."""
    _, fin = comun.ventana_noche(fecha)
    return [
        {"$match": {"inicio": {"$lt": fin}}},
        {"$sort": {"inicio": -1}},
        {"$group": {"_id": "$parcela_id", "inicio": {"$first": "$inicio"}, "fin": {"$first": "$fin"},
                    "lamina_mm": {"$first": "$lamina_mm"}, "origen": {"$first": "$origen"}}},
        {"$project": {"_id": 0, "parcela_id": "$_id", "inicio": 1, "fin": 1, "lamina_mm": 1, "origen": 1}},
        {"$sort": {"parcela_id": 1}},
    ]


def ultimo_riego(bd, fecha: date | str = comun.FECHA_NOCHE) -> dict[str, dict]:
    """{parcela_id: riego} con el último riego de cada parcela hasta el cierre de la noche."""
    return {r["parcela_id"]: r for r in bd.riegos.aggregate(pipeline_ultimo_riego(comun.a_fecha(fecha)))}


# --------------------------------------------------------------------------- frescura

def pipeline_ultima_lectura(ahora: datetime) -> list:
    return [
        {"$match": {"ts": {"$gt": ahora - timedelta(hours=FRESCURA_MAX_H), "$lte": ahora}}},
        {"$sort": {"ts": -1}},
        {"$limit": 1},
        {"$project": {"_id": 0, "ts": 1}},
    ]


def ultima_lectura(bd, ahora: datetime | str) -> datetime | None:
    """Momento de la última lectura hasta `ahora` (UTC con zona), o None si no hay en las últimas horas."""
    ahora = comun.a_utc(ahora)
    docs = list(bd.lecturas.aggregate(pipeline_ultima_lectura(ahora)))
    return comun.a_utc(docs[0]["ts"]) if docs else None


# --------------------------------------------------------------------------- noches con helada

def pipeline_noches_con_helada() -> list:
    """La mañana de una alerta es la fecha local de (inicio + 6 h): una alerta a las 20:00 es de la mañana siguiente."""
    return [
        {"$match": {"tipo": "helada"}},
        {"$group": {"_id": {"$dateToString": {
            "date": {"$dateAdd": {"startDate": "$inicio", "unit": "hour", "amount": 6}},
            "format": "%Y-%m-%d", "timezone": comun.ZONA}}}},
        {"$project": {"_id": 0, "fecha": "$_id"}},
        {"$sort": {"fecha": 1}},
    ]


def noches_con_helada(bd) -> list[date]:
    return [date.fromisoformat(d["fecha"]) for d in bd.alertas.aggregate(pipeline_noches_con_helada())]


# --------------------------------------------------------------------------- catálogo

def catalogo(bd) -> dict:
    """Fincas, parcelas y nodos con sus geometrías (para el mapa y para poner nombre a cada parcela)."""
    return {
        "fincas": list(bd.fincas.find({}, {"nombre": 1, "departamento": 1, "sistema_riego": 1, "tipo_suelo": 1}).sort("_id", 1)),
        "parcelas": list(bd.parcelas.find({}, {"finca_id": 1, "nombre": 1, "geometria": 1}).sort("_id", 1)),
        "nodos": list(bd.nodos.find({}, {"parcela_id": 1, "finca_id": 1, "ubicacion": 1, "estado": 1}).sort("_id", 1)),
    }
