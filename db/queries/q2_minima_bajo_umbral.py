"""Q2 - ¿Qué parcelas tuvieron una mínima por debajo del umbral de su estado fenológico?

Requisito: RF-01 y RF-04.   Técnica: $group + $lookup (lecturas -> parcelas -> fincas) con el umbral de la etapa.

Cómo se calcula:
    1. Etapa estimada de cada parcela en esa fecha (Q9) y el umbral de helada de esa etapa.
    2. $match + $group sobre las lecturas de la noche: la mínima de cada parcela.
    3. $set: temperatura del brote = mínima - Δ (configuracion.delta_brote_c) y el umbral de su
       parcela. El umbral se busca con $getField en un diccionario que armó el paso 1.
    4. $match: se queda con las parcelas cuyo brote quedó por debajo del umbral.
    5. $lookup a parcelas y fincas: nombre y departamento.
Como las alertas de helada, usa la etapa ESTIMADA (ADR-014).

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q2_minima_bajo_umbral --fecha 2026-10-05
"""

from datetime import date

from db.conexion import obtener_base, preparar_consola
from db.queries import comun, q9_etapa_por_grados_dia as q9

COLECCION = "lecturas"


def pipeline(fecha: date, etapas: dict[str, dict], delta_c: float) -> list:
    """`etapas` es el resultado de q9.etapas_estimadas: {parcela_id: {etapa, bbch, umbral_helada_c}}."""
    inicio, fin = comun.ventana_noche(fecha)
    umbrales = {p: e["umbral_helada_c"] for p, e in etapas.items()}
    nombres = {p: e["etapa"] for p, e in etapas.items()}
    return [
        {"$match": {"ts": {"$gte": inicio, "$lt": fin}}},
        {"$group": {"_id": "$meta.parcela_id", "minima_c": {"$min": "$temperatura_c"}}},
        {"$set": {
            "minima_brote_c": {"$subtract": ["$minima_c", delta_c]},
            "umbral_helada_c": {"$getField": {"field": "$_id", "input": {"$literal": umbrales}}},
            "etapa": {"$getField": {"field": "$_id", "input": {"$literal": nombres}}}}},
        # solo las que cruzaron el umbral (una etapa sin umbral no se evalúa)
        {"$match": {"umbral_helada_c": {"$ne": None}, "$expr": {"$lt": ["$minima_brote_c", "$umbral_helada_c"]}}},
        {"$lookup": {"from": "parcelas", "localField": "_id", "foreignField": "_id", "as": "parcela"}},
        {"$unwind": "$parcela"},
        {"$lookup": {"from": "fincas", "localField": "parcela.finca_id", "foreignField": "_id", "as": "finca"}},
        {"$unwind": "$finca"},
        {"$project": {"_id": 0, "parcela_id": "$_id", "finca": "$finca.nombre", "departamento": "$finca.departamento",
                      "etapa": 1, "umbral_helada_c": 1, "minima_c": 1,
                      "minima_brote_c": {"$round": ["$minima_brote_c", 2]},
                      "margen_c": {"$round": [{"$subtract": ["$minima_brote_c", "$umbral_helada_c"]}, 2]}}},
        {"$sort": {"parcela_id": 1}},
    ]


def consultar(bd, fecha: date | str = comun.FECHA_NOCHE) -> list[dict]:
    """Parcelas que bajaron del umbral de su etapa en la noche de la mañana `fecha`."""
    fecha = comun.a_fecha(fecha)
    etapas = q9.etapas_estimadas(bd, fecha)
    return list(bd[COLECCION].aggregate(pipeline(fecha, etapas, comun.configuracion(bd)["delta_brote_c"])))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--fecha", default=comun.FECHA_NOCHE.isoformat(), help="mañana de la noche (AAAA-MM-DD)")
    a = p.parse_args()
    bd = obtener_base()
    if a.mongosh:
        fecha = comun.a_fecha(a.fecha)
        print(comun.texto_mongosh(COLECCION, pipeline(fecha, q9.etapas_estimadas(bd, fecha),
                                                      comun.configuracion(bd)["delta_brote_c"])))
        return
    comun.imprimir_tabla(consultar(bd, a.fecha), ["parcela_id", "finca", "departamento", "etapa",
                                                  "umbral_helada_c", "minima_c", "minima_brote_c", "margen_c"])


if __name__ == "__main__":
    main()
