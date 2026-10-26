"""Q9 - ¿En qué etapa fenológica estimada está cada parcela según los grados-día acumulados?

Requisito: RF-16 y RF-18.   Técnica: $group + $setWindowFields (suma acumulada) + $lookup a variedades.

Cómo se calcula (la MISMA regla que el simulador, ver docs/simulador.md):
    1. Máxima y mínima de cada nodo en cada día local (hora de Argentina).
    2. Máxima y mínima del día de la parcela: promedio de sus 2 nodos.
    3. Grados-día del día = max(0, min((Tmáx + Tmín) / 2, tope) - base), con base 10 °C y tope 32 °C.
    4. Se suman en orden: la etapa de un día usa los grados-día acumulados hasta el día ANTERIOR.
    5. A eso se le restan los 70 grados-día hasta la brotación y se busca, en `variedades.etapas`,
       la última etapa cuyo `gd_desde_brotacion` no lo supera.
    6. Si hay una observación manual hasta esa fecha, se informa aparte (`bbch_observada`) y la
       etapa efectiva (`bbch`, `etapa`) es la observada; si no, la estimada (RF-18).
Para los cálculos de helada (Q2 y Q10) se usa la estimada, igual que las alertas (ADR-014).

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q9_etapa_por_grados_dia --fecha 2026-10-05
    python -m db.queries.q9_etapa_por_grados_dia --parcela P-SR-1 --todos     # toda la temporada
    python -m db.queries.q9_etapa_por_grados_dia --mongosh                    # la consulta para mongosh
"""

from datetime import date, timedelta

from db.conexion import obtener_base, preparar_consola
from db.queries import comun

COLECCION = "lecturas"


def pipeline(fecha: date = comun.FECHA_NOCHE, parcela_id: str | None = None, todos: bool = False) -> list:
    """Las etapas de la consulta. Con `todos` devuelve todos los días hasta `fecha`; si no, solo `fecha`."""
    hasta = comun.medianoche_local(fecha + timedelta(days=1))  # fin del día `fecha`, en UTC
    filtro = {"ts": {"$lt": hasta}}
    if parcela_id:
        filtro["meta.parcela_id"] = parcela_id

    etapas = [
        # 1) Solo las lecturas hasta el fin de la fecha pedida (y de la parcela, si se pide una)
        {"$match": filtro},
        # 2) Máxima y mínima de cada nodo en cada día local
        {
            "$group": {
                "_id": {
                    "parcela": "$meta.parcela_id",
                    "nodo": "$meta.nodo_id",
                    "dia": {"$dateTrunc": {"date": "$ts", "unit": "day", "timezone": comun.ZONA}},
                },
                "max": {"$max": "$temperatura_c"},
                "min": {"$min": "$temperatura_c"},
            }
        },
        # 3) Máxima y mínima del día de la parcela: promedio de sus nodos
        {
            "$group": {
                "_id": {"parcela": "$_id.parcela", "dia": "$_id.dia"},
                "tmax": {"$avg": "$max"},
                "tmin": {"$avg": "$min"},
            }
        },
        # 4) Datos de la variedad de cada parcela (base, tope, brotación y etapas)
        {"$lookup": {"from": "parcelas", "localField": "_id.parcela", "foreignField": "_id", "as": "parcela"}},
        {"$unwind": "$parcela"},
        {
            "$lookup": {
                "from": "variedades",
                "localField": "parcela.variedad_id",
                "foreignField": "_id",
                "as": "variedad",
            }
        },
        {"$unwind": "$variedad"},
        # 5) Grados-día del día
        {
            "$set": {
                "gd": {
                    "$max": [
                        0,
                        {
                            "$subtract": [
                                {
                                    "$min": [
                                        {"$divide": [{"$add": ["$tmax", "$tmin"]}, 2]},
                                        "$variedad.grados_dia.tope_c",
                                    ]
                                },
                                "$variedad.grados_dia.base_c",
                            ]
                        },
                    ]
                }
            }
        },
        # 6) Suma acumulada por parcela, en orden de día: hasta ayer (sin contar hoy) y hasta hoy
        {
            "$setWindowFields": {
                "partitionBy": "$_id.parcela",
                "sortBy": {"_id.dia": 1},
                "output": {
                    "gd_hasta_ayer": {"$sum": "$gd", "window": {"documents": ["unbounded", -1]}},
                    "gd_acumulados": {"$sum": "$gd", "window": {"documents": ["unbounded", "current"]}},
                },
            }
        },
    ]
    if not todos:
        etapas.append({"$match": {"_id.dia": comun.medianoche_local(fecha)}})
    etapas += [
        # 7) Etapa estimada: la última cuyo gd_desde_brotacion no supera lo acumulado menos la brotación
        {
            "$set": {
                "etapa_estimada": {
                    "$last": {
                        "$filter": {
                            "input": "$variedad.etapas",
                            "as": "e",
                            "cond": {
                                "$lte": [
                                    "$$e.gd_desde_brotacion",
                                    {"$subtract": ["$gd_hasta_ayer", "$variedad.grados_dia.hasta_brotacion"]},
                                ]
                            },
                        }
                    }
                }
            }
        },
        # 8) Última observación manual hasta el fin de ese día
        {
            "$lookup": {
                "from": "observaciones_fenologicas",
                "let": {"p": "$_id.parcela", "d": "$_id.dia"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$parcela_id", "$$p"]},
                                    {"$lt": ["$fecha", {"$dateAdd": {"startDate": "$$d", "unit": "day", "amount": 1}}]},
                                ]
                            }
                        }
                    },
                    {"$sort": {"fecha": -1}},
                    {"$limit": 1},
                ],
                "as": "obs",
            }
        },
        {"$set": {"obs": {"$first": "$obs"}}},
        # 9) A qué etapa corresponde el BBCH observado
        {
            "$set": {
                "etapa_observada": {
                    "$first": {
                        "$filter": {
                            "input": "$variedad.etapas",
                            "as": "e",
                            "cond": {
                                "$and": [
                                    {"$lte": ["$$e.bbch_desde", "$obs.etapa_bbch"]},
                                    {"$gte": ["$$e.bbch_hasta", "$obs.etapa_bbch"]},
                                ]
                            },
                        }
                    }
                }
            }
        },
        # 10) Salida: la efectiva es la observada si existe, si no la estimada
        {
            "$project": {
                "_id": 0,
                "parcela_id": "$_id.parcela",
                "fecha": "$_id.dia",
                "gd_dia": {"$round": ["$gd", 2]},
                "gd_acumulados": {"$round": ["$gd_acumulados", 2]},
                "gd_hasta_ayer": {"$round": ["$gd_hasta_ayer", 2]},
                "bbch_estimada": "$etapa_estimada.bbch_desde",
                "etapa_estimada": "$etapa_estimada.nombre",
                "umbral_helada_c": "$etapa_estimada.umbral_helada_c",
                "bbch_observada": {"$ifNull": ["$etapa_observada.bbch_desde", None]},  # null si no hay observación
                "fecha_observacion": {"$ifNull": ["$obs.fecha", None]},
                "bbch": {"$ifNull": ["$etapa_observada.bbch_desde", "$etapa_estimada.bbch_desde"]},
                "etapa": {"$ifNull": ["$etapa_observada.nombre", "$etapa_estimada.nombre"]},
            }
        },
        {"$sort": {"parcela_id": 1, "fecha": 1}},
    ]
    return etapas


def consultar(
    bd, fecha: date | str = comun.FECHA_NOCHE, parcela_id: str | None = None, todos: bool = False
) -> list[dict]:
    """Etapa de cada parcela en `fecha` (o de todos los días hasta `fecha` si `todos`)."""
    etapas = pipeline(comun.a_fecha(fecha), parcela_id, todos)
    return list(bd[COLECCION].aggregate(etapas, allowDiskUse=True))


def etapas_estimadas(bd, fecha: date | str = comun.FECHA_NOCHE) -> dict[str, dict]:
    """{parcela_id: {"etapa": nombre, "bbch": n, "umbral_helada_c": °C o None}} con la etapa ESTIMADA de
    cada parcela en `fecha`. La usan Q2 y Q10 (la helada se mide con la estimada, como las alertas)."""
    return {
        f["parcela_id"]: {
            "etapa": f["etapa_estimada"],
            "bbch": f["bbch_estimada"],
            "umbral_helada_c": f.get("umbral_helada_c"),
        }
        for f in consultar(bd, fecha)
    }


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--fecha", default=comun.FECHA_NOCHE.isoformat(), help="día (AAAA-MM-DD, por defecto 2026-10-05)")
    p.add_argument("--parcela", help="solo esa parcela (por ejemplo P-SR-1)")
    p.add_argument("--todos", action="store_true", help="todos los días hasta la fecha")
    a = p.parse_args()
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline(comun.a_fecha(a.fecha), a.parcela, a.todos)))
        return
    comun.imprimir_tabla(
        consultar(obtener_base(), a.fecha, a.parcela, a.todos),
        [
            "parcela_id",
            "fecha",
            "gd_acumulados",
            "bbch_estimada",
            "etapa_estimada",
            "umbral_helada_c",
            "bbch_observada",
            "bbch",
        ],
    )


if __name__ == "__main__":
    main()
