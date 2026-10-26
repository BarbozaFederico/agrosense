"""Q5 - ¿Qué nodos no reportaron en los últimos 30 minutos?

Requisito: RF-06.   Técnica: $lookup (nodos -> lecturas) + $match.

El "ahora" es un parámetro (ADR-004): el dashboard lo elige con un selector, así la consulta muestra
cómo estaba la base ese día. Los 30 minutos salen de `configuracion.nodo_inactivo_min`.

Cómo se calcula:
    1. Se parte de `nodos` (así un nodo sin ninguna lectura también aparece).
    2. $lookup a `lecturas`: la última lectura de ese nodo hasta el "ahora" (ordena por ts de forma
       descendente y se queda con una). Sin un índice propio recorre todos los grupos de lecturas de
       cada nodo (5.053 documentos examinados); con {meta.nodo_id: 1, ts: -1} lee 433 (ADR-015).
    3. $set: minutos desde esa última lectura hasta el "ahora".
    4. $match: los que pasaron del límite, o no tienen ninguna lectura.

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q5_nodos_sin_reportar --ahora 2026-11-12T21:00:00Z
"""

from datetime import datetime

from db.conexion import obtener_base, preparar_consola
from db.queries import comun

COLECCION = "nodos"


def pipeline(ahora: datetime, minutos: int) -> list:
    return [
        {
            "$lookup": {
                "from": "lecturas",
                "localField": "_id",
                "foreignField": "meta.nodo_id",
                "pipeline": [
                    {"$match": {"ts": {"$lte": ahora}}},
                    {"$sort": {"ts": -1}},
                    {"$limit": 1},
                    {"$project": {"_id": 0, "ts": 1}},
                ],
                "as": "ultima",
            }
        },
        {"$set": {"ultima_lectura": {"$ifNull": [{"$first": "$ultima.ts"}, None]}}},
        {
            "$set": {
                "minutos_sin_reportar": {
                    "$cond": [
                        {"$eq": ["$ultima_lectura", None]},
                        None,
                        {"$round": [{"$divide": [{"$subtract": [ahora, "$ultima_lectura"]}, 60000]}, 0]},
                    ]
                }
            }
        },
        # sin ninguna lectura, o la última es más vieja que el límite
        {"$match": {"$or": [{"ultima_lectura": None}, {"minutos_sin_reportar": {"$gt": minutos}}]}},
        {
            "$project": {
                "_id": 0,
                "nodo_id": "$_id",
                "parcela_id": 1,
                "finca_id": 1,
                "estado": 1,
                "ultima_lectura": 1,
                "minutos_sin_reportar": 1,
            }
        },
        {"$sort": {"nodo_id": 1}},
    ]


def consultar(bd, ahora: datetime | str = comun.AHORA, minutos: int | None = None) -> list[dict]:
    """Nodos sin lecturas en los últimos `minutos` (por defecto, el límite de la configuración) antes de `ahora`."""
    if minutos is None:
        minutos = comun.configuracion(bd)["nodo_inactivo_min"]
    return list(bd[COLECCION].aggregate(pipeline(comun.a_utc(ahora), minutos)))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument(
        "--ahora",
        default=comun.AHORA.isoformat().replace("+00:00", "Z"),
        help="el 'ahora' en UTC, por ejemplo 2026-11-12T21:00:00Z",
    )
    p.add_argument("--minutos", type=int, help="límite en minutos (por defecto el de la configuración)")
    a = p.parse_args()
    bd = obtener_base()
    minutos = a.minutos if a.minutos is not None else comun.configuracion(bd)["nodo_inactivo_min"]
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline(comun.a_utc(a.ahora), minutos)))
        return
    comun.imprimir_tabla(
        consultar(bd, a.ahora, minutos), ["nodo_id", "parcela_id", "estado", "ultima_lectura", "minutos_sin_reportar"]
    )


if __name__ == "__main__":
    main()
