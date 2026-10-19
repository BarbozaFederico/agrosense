"""Q1 - ¿Cuántas horas estuvo cada parcela por debajo de 0 °C en una noche?

Requisito: RF-03 y RF-04.   Técnica: $group + $setWindowFields (con $integral).

Cómo se calcula:
    1. Se toman las lecturas de la noche: de las 18:00 del día anterior a las 12:00 de la fecha,
       hora de Argentina (ADR-014).
    2. $group: en cada instante, la temperatura de la parcela es la del nodo MÁS FRÍO (igual que las
       alertas de helada).
    3. $setWindowFields con $integral: se "suma el tiempo" en que esa temperatura estuvo bajo cero.
       Se integra un indicador que vale 1 cuando hace menos de 0 °C y 0 si no; como las lecturas
       son cada 5 minutos, cada lectura bajo cero aporta 5 minutos.
    4. $group: se queda con el total de cada parcela (el acumulado final) y la mínima.

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q1_horas_bajo_cero --fecha 2026-10-05
    python -m db.queries.q1_horas_bajo_cero --fecha 2026-10-05 --mongosh
"""

from datetime import date

from db.conexion import obtener_base, preparar_consola
from db.queries import comun

COLECCION = "lecturas"


def pipeline(fecha: date = comun.FECHA_NOCHE, parcela_id: str | None = None) -> list:
    inicio, fin = comun.ventana_noche(fecha)
    filtro = {"ts": {"$gte": inicio, "$lt": fin}}
    if parcela_id:
        filtro["meta.parcela_id"] = parcela_id
    return [
        {"$match": filtro},
        # temperatura de la parcela en cada instante: la del nodo más frío
        {"$group": {"_id": {"parcela": "$meta.parcela_id", "ts": "$ts"}, "tmin": {"$min": "$temperatura_c"}}},
        # tiempo acumulado bajo cero, en horas
        {"$setWindowFields": {
            "partitionBy": "$_id.parcela", "sortBy": {"_id.ts": 1},
            "output": {"horas": {
                "$integral": {"input": {"$cond": [{"$lt": ["$tmin", 0]}, 1, 0]}, "unit": "hour"},
                "window": {"range": ["unbounded", "current"], "unit": "hour"}}}}},
        # el total de la noche es el último valor acumulado
        {"$group": {"_id": "$_id.parcela", "horas_bajo_cero": {"$max": "$horas"},
                    "minima_c": {"$min": "$tmin"}}},
        {"$lookup": {"from": "parcelas", "localField": "_id", "foreignField": "_id", "as": "parcela"}},
        {"$unwind": "$parcela"},
        {"$project": {"_id": 0, "parcela_id": "$_id", "finca_id": "$parcela.finca_id",
                      "horas_bajo_cero": {"$round": ["$horas_bajo_cero", 2]}, "minima_c": 1}},
        {"$sort": {"horas_bajo_cero": -1, "parcela_id": 1}},
    ]


def consultar(bd, fecha: date | str = comun.FECHA_NOCHE, parcela_id: str | None = None) -> list[dict]:
    """Horas bajo 0 °C de cada parcela en la noche de la mañana `fecha`."""
    return list(bd[COLECCION].aggregate(pipeline(comun.a_fecha(fecha), parcela_id)))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--fecha", default=comun.FECHA_NOCHE.isoformat(), help="mañana de la noche (AAAA-MM-DD)")
    p.add_argument("--parcela", help="solo esa parcela")
    a = p.parse_args()
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline(comun.a_fecha(a.fecha), a.parcela)))
        return
    comun.imprimir_tabla(consultar(obtener_base(), a.fecha, a.parcela),
                         ["parcela_id", "finca_id", "horas_bajo_cero", "minima_c"])


if __name__ == "__main__":
    main()
