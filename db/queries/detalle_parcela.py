"""Consultas de apoyo de la pantalla "Detalle de parcela" del dashboard (ADR-019).

No son parte de Q1 a Q10 (la pantalla también usa Q1, Q6, Q7, Q9 y Q10 tal cual): traen lo que
la curva de la noche y la lista de riegos necesitan. Ninguna escribe en la base.
    curva_de_la_noche    lecturas de temperatura de la parcela en la noche, por nodo (la curva)
    riegos_recientes     los últimos riegos de la parcela hasta el cierre de la noche

Una noche va de las 18:00 del día anterior a las 12:00 de la mañana elegida, hora de Argentina (ADR-014).
"""

from datetime import date, datetime

from db.queries import comun

COLECCION_CURVA = "lecturas"
COLECCION_RIEGOS = "riegos"
RIEGOS_MAXIMOS = 8


def pipeline_curva_de_la_noche(fecha: date, parcela_id: str) -> list:
    """Temperatura de cada nodo de la parcela cada 5 minutos, de las 18:00 a las 12:00 (hora de Argentina)."""
    inicio, fin = comun.ventana_noche(fecha)
    return [
        {"$match": {"meta.parcela_id": parcela_id, "ts": {"$gte": inicio, "$lt": fin}}},
        {"$project": {"_id": 0, "ts": 1, "nodo_id": "$meta.nodo_id", "temperatura_c": 1}},
        {"$sort": {"ts": 1, "nodo_id": 1}},
    ]


def curva_de_la_noche(bd, fecha: date | str, parcela_id: str) -> list[dict]:
    return list(bd[COLECCION_CURVA].aggregate(pipeline_curva_de_la_noche(comun.a_fecha(fecha), parcela_id)))


def pipeline_riegos_recientes(fecha: date, parcela_id: str, limite: int = RIEGOS_MAXIMOS) -> list:
    """Los últimos `limite` riegos de la parcela que empezaron antes del cierre de la noche."""
    _, fin = comun.ventana_noche(fecha)
    return [
        {"$match": {"parcela_id": parcela_id, "inicio": {"$lt": fin}}},
        {"$sort": {"inicio": -1}},
        {"$limit": limite},
        {"$project": {"_id": 0, "inicio": 1, "fin": 1, "lamina_mm": 1, "litros": 1, "origen": 1, "sistema": 1}},
    ]


def riegos_recientes(bd, fecha: date | str, parcela_id: str, limite: int = RIEGOS_MAXIMOS) -> list[dict]:
    return list(bd[COLECCION_RIEGOS].aggregate(pipeline_riegos_recientes(comun.a_fecha(fecha), parcela_id, limite)))


def cierre_de_la_noche(fecha: date) -> datetime:
    """El "ahora" de la pantalla: las 12:00 de la mañana elegida, como UTC con zona (igual que Resumen, ADR-018)."""
    return comun.ventana_noche(fecha)[1]
