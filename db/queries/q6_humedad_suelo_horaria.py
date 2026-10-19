"""Q6 - ¿Cuál es la humedad de suelo promedio por hora de una parcela en las últimas 24 horas?

Requisito: RF-03.   Técnica: $match + $group con $dateTrunc (agregación sobre lecturas).

El "ahora" es un parámetro (ADR-004). Se muestran las 24 horas COMPLETAS anteriores a la hora en curso
(si son las 06:30, desde las 06:00 de ayer hasta las 06:00 de hoy): así todas las filas tienen las
mismas lecturas (2 nodos x 12 lecturas por hora).

Cómo se calcula:
    1. $match: las lecturas de la parcela en esa ventana.
    2. $group: se agrupan por hora local ($dateTrunc, hora de Argentina) y se promedia la humedad de
       suelo de los dos nodos.
    3. $sort por hora.

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q6_humedad_suelo_horaria --parcela P-SR-1 --ahora 2027-01-20T15:00:00Z
"""

from datetime import datetime, timedelta

from db.conexion import obtener_base, preparar_consola
from db.queries import comun

COLECCION = "lecturas"
PARCELA = "P-SR-1"


def pipeline(ahora: datetime, parcela_id: str = PARCELA, horas: int = 24) -> list:
    fin = ahora.replace(minute=0, second=0, microsecond=0)               # la hora en curso, redondeada hacia abajo
    inicio = fin - timedelta(hours=horas)
    return [
        {"$match": {"meta.parcela_id": parcela_id, "ts": {"$gte": inicio, "$lt": fin}}},
        {"$group": {"_id": {"$dateTrunc": {"date": "$ts", "unit": "hour", "timezone": comun.ZONA}},
                    "humedad_suelo_pct": {"$avg": "$humedad_suelo_pct"}, "lecturas": {"$sum": 1}}},
        {"$project": {"_id": 0, "hora": "$_id", "humedad_suelo_pct": {"$round": ["$humedad_suelo_pct", 2]},
                      "lecturas": 1}},
        {"$sort": {"hora": 1}},
    ]


def consultar(bd, ahora: datetime | str = comun.AHORA, parcela_id: str = PARCELA, horas: int = 24) -> list[dict]:
    """Humedad de suelo promedio de cada una de las últimas `horas` horas completas."""
    return list(bd[COLECCION].aggregate(pipeline(comun.a_utc(ahora), parcela_id, horas)))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--ahora", default=comun.AHORA.isoformat().replace("+00:00", "Z"), help="el 'ahora' en UTC")
    p.add_argument("--parcela", default=PARCELA)
    p.add_argument("--horas", type=int, default=24)
    a = p.parse_args()
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline(comun.a_utc(a.ahora), a.parcela, a.horas)))
        return
    comun.imprimir_tabla(consultar(obtener_base(), a.ahora, a.parcela, a.horas),
                         ["hora", "humedad_suelo_pct", "lecturas"])


if __name__ == "__main__":
    main()
