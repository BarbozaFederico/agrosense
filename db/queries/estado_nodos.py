"""Consulta de apoyo de la pantalla "Estado de nodos" del dashboard (ADR-021).

No es parte de Q1 a Q10: Q5 devuelve solo los nodos que NO reportan, y la pantalla necesita la lista de los 12 con
su último reporte. Es la misma búsqueda de Q5 (de `nodos` a su última lectura hasta el "ahora") sin el filtro final;
se arma con las primeras etapas de Q5 para que las dos nunca discrepen, y una prueba lo comprueba.
No escribe en la base.
"""

from datetime import datetime

from db.queries import comun, q5_nodos_sin_reportar as q5

ETAPAS_DE_Q5_COMPARTIDAS = 3        # $lookup a la última lectura, `ultima_lectura` y `minutos_sin_reportar`


def pipeline_ultimo_reporte(ahora: datetime) -> list:
    """Cada nodo con el momento de su última lectura hasta `ahora` y los minutos que pasaron desde entonces."""
    compartidas = q5.pipeline(ahora, 0)[:ETAPAS_DE_Q5_COMPARTIDAS]      # el límite no se usa antes del $match
    return compartidas + [
        {"$project": {"_id": 0, "nodo_id": "$_id", "parcela_id": 1, "finca_id": 1, "estado": 1,
                      "ultima_lectura": 1, "minutos_sin_reportar": 1}},
        {"$sort": {"nodo_id": 1}},
    ]


def ultimo_reporte(bd, ahora: datetime | str) -> list[dict]:
    """Los nodos con su último reporte hasta `ahora` (UTC con zona o texto ISO)."""
    return list(bd.nodos.aggregate(pipeline_ultimo_reporte(comun.a_utc(ahora))))
