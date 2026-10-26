"""Q7 - ¿Cuántos litros se regaron por parcela en la semana?

Requisito: RF-05.   Técnica: $group con $dateTrunc (semana).

La semana va de lunes a domingo, en hora de Argentina (ADR-014). Los litros ya están calculados en cada
riego (lámina en mm x superficie en ha x 10.000, ADR-006), así que acá solo se suman.

Cómo se calcula:
    1. $match opcional: una parcela y/o un rango de fechas.
    2. $group por parcela y semana ($dateTrunc con startOfWeek lunes): suma de litros, de láminas y
       cantidad de riegos.
    3. $sort.

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q7_litros_por_semana --parcela P-SR-1
"""

from datetime import datetime

from db.conexion import obtener_base, preparar_consola
from db.queries import comun

COLECCION = "riegos"


def pipeline(parcela_id: str | None = None, desde: datetime | None = None, hasta: datetime | None = None) -> list:
    filtro: dict = {}
    if parcela_id:
        filtro["parcela_id"] = parcela_id
    if desde or hasta:
        filtro["inicio"] = {**({"$gte": desde} if desde else {}), **({"$lt": hasta} if hasta else {})}
    return [
        {"$match": filtro},
        {
            "$group": {
                "_id": {
                    "parcela": "$parcela_id",
                    "semana": {
                        "$dateTrunc": {
                            "date": "$inicio",
                            "unit": "week",
                            "startOfWeek": "monday",
                            "timezone": comun.ZONA,
                        }
                    },
                },
                "litros": {"$sum": "$litros"},
                "lamina_mm": {"$sum": "$lamina_mm"},
                "riegos": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "parcela_id": "$_id.parcela",
                "semana": "$_id.semana",
                "litros": 1,
                "lamina_mm": {"$round": ["$lamina_mm", 1]},
                "riegos": 1,
            }
        },
        {"$sort": {"parcela_id": 1, "semana": 1}},
    ]


def consultar(
    bd, parcela_id: str | None = None, desde: datetime | str | None = None, hasta: datetime | str | None = None
) -> list[dict]:
    """Litros regados por parcela y semana (lunes a domingo, hora de Argentina)."""
    return list(
        bd[COLECCION].aggregate(
            pipeline(parcela_id, comun.a_utc(desde) if desde else None, comun.a_utc(hasta) if hasta else None)
        )
    )


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--parcela", help="solo esa parcela")
    p.add_argument("--desde", help="desde (UTC, por ejemplo 2026-12-01T00:00:00Z)")
    p.add_argument("--hasta", help="hasta (UTC, sin incluir)")
    a = p.parse_args()
    desde = comun.a_utc(a.desde) if a.desde else None
    hasta = comun.a_utc(a.hasta) if a.hasta else None
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline(a.parcela, desde, hasta)))
        return
    comun.imprimir_tabla(
        consultar(obtener_base(), a.parcela, desde, hasta), ["parcela_id", "semana", "litros", "lamina_mm", "riegos"]
    )


if __name__ == "__main__":
    main()
