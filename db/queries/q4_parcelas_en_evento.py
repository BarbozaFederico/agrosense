"""Q4 - ¿Qué parcelas quedan dentro del polígono de un evento climático?

Requisito: RF-07 y RF-08.   Técnica: $geoIntersects (índice 2dsphere en parcelas.geometria).

Primero se lee el evento (su polígono, en `eventos_climaticos.area`) y después se buscan las parcelas
cuyo polígono se cruza con el del evento. "Dentro" se interpreta como "toca o está dentro": una
parcela que el evento cubre solo en parte también se considera afectada.

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q4_parcelas_en_evento
    python -m db.queries.q4_parcelas_en_evento --evento 5eed00000000000000000001
"""

from bson import ObjectId

from db.conexion import obtener_base, preparar_consola
from db.queries import comun

COLECCION = "parcelas"


def pipeline(area: dict) -> list:
    return [
        {"$match": {"geometria": {"$geoIntersects": {"$geometry": area}}}},
        {"$lookup": {"from": "fincas", "localField": "finca_id", "foreignField": "_id", "as": "finca"}},
        {"$unwind": "$finca"},
        {"$project": {"_id": 0, "parcela_id": "$_id", "nombre": 1, "finca": "$finca.nombre",
                      "departamento": "$finca.departamento", "superficie_ha": 1}},
        {"$sort": {"parcela_id": 1}},
    ]


def buscar_evento(bd, evento_id: str | ObjectId | None = None) -> dict:
    """El evento pedido, o el más reciente si no se indica."""
    if evento_id:
        evento = bd.eventos_climaticos.find_one({"_id": ObjectId(evento_id)})
    else:
        evento = next(bd.eventos_climaticos.find().sort("inicio", -1).limit(1), None)
    if evento is None:
        raise SystemExit("No hay eventos climáticos: corré primero  python -m db.seeds.cargar")
    return evento


def consultar(bd, evento_id: str | ObjectId | None = None) -> list[dict]:
    """Parcelas que se cruzan con el área del evento."""
    return list(bd[COLECCION].aggregate(pipeline(buscar_evento(bd, evento_id)["area"])))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--evento", help="_id del evento (por defecto el más reciente)")
    a = p.parse_args()
    bd = obtener_base()
    evento = buscar_evento(bd, a.evento)
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline(evento["area"])))
        return
    print(f"Evento {evento['_id']} ({evento['tipo']}), del {comun.a_hora_local(evento['inicio']):%d/%m/%Y %H:%M} "
          f"al {comun.a_hora_local(evento['fin']):%d/%m/%Y %H:%M} (hora de Argentina)")
    comun.imprimir_tabla(consultar(bd, evento["_id"]),
                         ["parcela_id", "nombre", "finca", "departamento", "superficie_ha"])


if __name__ == "__main__":
    main()
