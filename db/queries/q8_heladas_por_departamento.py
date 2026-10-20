"""Q8 - ¿Cuántos eventos de helada hubo por departamento y por semana?

Requisito: RF-04 y RF-08.   Técnica: $group + $lookup (alertas -> parcelas -> fincas).

Las alertas guardan solo la parcela (ADR-003: referencias, no copias); el departamento se obtiene con dos
$lookup encadenados. Un "evento de helada" es una alerta de helada: cada parcela que cruza el umbral abre
la suya, así que una noche en una finca de 2 parcelas cuenta 2 eventos y 2 parcelas afectadas.

Cómo se calcula:
    1. $match: alertas de tipo "helada".
    2. $lookup a parcelas y a fincas: de la alerta a su departamento.
    3. $group por departamento y semana de inicio (lunes a domingo, hora de Argentina): cantidad de
       alertas, parcelas afectadas y la mínima del brote.
    4. $sort.

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q8_heladas_por_departamento
"""

from db.conexion import obtener_base, preparar_consola
from db.queries import comun

COLECCION = "alertas"


def pipeline() -> list:
    return [
        {"$match": {"tipo": "helada"}},
        {"$lookup": {"from": "parcelas", "localField": "parcela_id", "foreignField": "_id", "as": "parcela"}},
        {"$unwind": "$parcela"},
        {"$lookup": {"from": "fincas", "localField": "parcela.finca_id", "foreignField": "_id", "as": "finca"}},
        {"$unwind": "$finca"},
        {"$group": {"_id": {"departamento": "$finca.departamento",
                            "semana": {"$dateTrunc": {"date": "$inicio", "unit": "week", "startOfWeek": "monday",
                                                      "timezone": comun.ZONA}}},
                    "alertas": {"$sum": 1}, "parcelas": {"$addToSet": "$parcela_id"},
                    "minima_brote_c": {"$min": "$valor_extremo"}}},
        {"$project": {"_id": 0, "departamento": "$_id.departamento", "semana": "$_id.semana", "alertas": 1,
                      "parcelas_afectadas": {"$size": "$parcelas"}, "minima_brote_c": 1}},
        {"$sort": {"semana": 1, "departamento": 1}},
    ]


def consultar(bd) -> list[dict]:
    """Alertas de helada por departamento y semana."""
    return list(bd[COLECCION].aggregate(pipeline()))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    a = p.parse_args()
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline()))
        return
    comun.imprimir_tabla(consultar(obtener_base()), ["semana", "departamento", "alertas", "parcelas_afectadas",
                                                     "minima_brote_c"])


if __name__ == "__main__":
    main()
