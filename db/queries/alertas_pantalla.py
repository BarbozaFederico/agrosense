"""Consultas de apoyo de la pantalla "Alertas" del dashboard (ADR-020).

No son parte de Q1 a Q10 (la pantalla también usa Q8 tal cual): traen las alertas de ambos tipos (helada y riego)
y el nombre de las etapas. Ninguna escribe en la base.
    alertas_de_la_noche   alertas que se solapan con la noche, abiertas o cerradas
    historial             alertas de la temporada que empezaron antes del cierre de la noche
    etapas_del_malbec     nombre de cada etapa BBCH (las alertas guardan solo el número, ADR-006)

Una noche va de las 18:00 del día anterior a las 12:00 de la mañana elegida, hora de Argentina (ADR-014).
"""

from datetime import date

from db.queries import comun

CAMPOS = {
    "_id": 0,
    "tipo": 1,
    "parcela_id": 1,
    "estado": 1,
    "inicio": 1,
    "fin": 1,
    "etapa_bbch": 1,
    "umbral": 1,
    "valor_extremo": 1,
    "riesgo": 1,
}
HISTORIAL_MAXIMO = 200


def pipeline_alertas_de_la_noche(fecha: date) -> list:
    """Alertas de cualquier tipo que empezaron antes del cierre de la noche y no terminaron antes de su comienzo."""
    inicio, fin = comun.ventana_noche(fecha)
    return [
        {"$match": {"inicio": {"$lt": fin}, "$or": [{"fin": None}, {"fin": {"$gte": inicio}}]}},
        {"$project": CAMPOS},
        {"$sort": {"inicio": 1, "parcela_id": 1}},
    ]


def alertas_de_la_noche(bd, fecha: date | str = comun.FECHA_NOCHE) -> list[dict]:
    return list(bd.alertas.aggregate(pipeline_alertas_de_la_noche(comun.a_fecha(fecha))))


def pipeline_historial(fecha: date, limite: int = HISTORIAL_MAXIMO) -> list:
    """Las últimas `limite` alertas que empezaron antes del cierre de la noche, las más recientes primero."""
    _, fin = comun.ventana_noche(fecha)
    return [
        {"$match": {"inicio": {"$lt": fin}}},
        {"$sort": {"inicio": -1, "parcela_id": 1}},
        {"$limit": limite},
        {"$project": CAMPOS},
    ]


def historial(bd, fecha: date | str = comun.FECHA_NOCHE, limite: int = HISTORIAL_MAXIMO) -> list[dict]:
    return list(bd.alertas.aggregate(pipeline_historial(comun.a_fecha(fecha), limite)))


def etapas_del_malbec(bd) -> list[dict]:
    """Las etapas de `variedades` ("malbec") con su rango de BBCH y su nombre."""
    doc = bd.variedades.find_one(
        {"_id": "malbec"}, {"etapas.bbch_desde": 1, "etapas.bbch_hasta": 1, "etapas.nombre": 1}
    )
    return doc["etapas"] if doc else []
