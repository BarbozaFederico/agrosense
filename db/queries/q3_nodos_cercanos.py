"""Q3 - ¿Qué nodos están más cerca de un punto dado?

Requisito: RF-07.   Técnica: $geoNear (índice 2dsphere en nodos.ubicacion).

$geoNear tiene que ser la PRIMERA etapa de la tubería y necesita un índice 2dsphere (se crea con
python -m db.indexes.crear_indices). Devuelve los documentos ordenados del más cercano al más lejano,
con la distancia en metros. Se hace sobre `nodos` y no sobre `lecturas` porque las series
temporales solo aceptan índices de puntos y no devuelven la distancia (spike del 14/10/2026).

Cómo correrla (desde la raíz del repo):
    python -m db.queries.q3_nodos_cercanos --lon -68.33 --lat -34.61 --cantidad 4
"""

from db.conexion import obtener_base, preparar_consola
from db.queries import comun
from db.seeds.ubicaciones import centro_parcela

COLECCION = "nodos"
PUNTO = tuple(centro_parcela("P-SR-1"))  # (longitud, latitud): el centro de la parcela P-SR-1


def pipeline(punto: tuple[float, float] = PUNTO, cantidad: int = 4, maxima_m: float | None = None) -> list:
    geo = {"near": {"type": "Point", "coordinates": list(punto)}, "distanceField": "distancia_m", "spherical": True}
    if maxima_m is not None:
        geo["maxDistance"] = maxima_m
    return [
        {"$geoNear": geo},
        {"$limit": cantidad},
        {
            "$project": {
                "_id": 0,
                "nodo_id": "$_id",
                "parcela_id": 1,
                "finca_id": 1,
                "estado": 1,
                "distancia_m": {"$round": ["$distancia_m", 1]},
            }
        },
    ]


def consultar(bd, punto: tuple[float, float] = PUNTO, cantidad: int = 4, maxima_m: float | None = None) -> list[dict]:
    """Los `cantidad` nodos más cercanos a `punto` (longitud, latitud), con la distancia en metros."""
    return list(bd[COLECCION].aggregate(pipeline(punto, cantidad, maxima_m)))


def main() -> None:
    preparar_consola()
    p = comun.parser(__doc__.splitlines()[0])
    p.add_argument("--lon", type=float, default=PUNTO[0], help="longitud (por defecto el centro de P-SR-1)")
    p.add_argument("--lat", type=float, default=PUNTO[1], help="latitud")
    p.add_argument("--cantidad", type=int, default=4)
    p.add_argument("--maxima", type=float, help="distancia máxima en metros")
    a = p.parse_args()
    if a.mongosh:
        print(comun.texto_mongosh(COLECCION, pipeline((a.lon, a.lat), a.cantidad, a.maxima)))
        return
    comun.imprimir_tabla(
        consultar(obtener_base(), (a.lon, a.lat), a.cantidad, a.maxima),
        ["nodo_id", "parcela_id", "finca_id", "distancia_m", "estado"],
    )


if __name__ == "__main__":
    main()
