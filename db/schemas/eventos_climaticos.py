"""Esquema de `eventos_climaticos` (colección común). Campos en docs/modelo-datos.md, sección 3.7.

Es colección común porque guarda polígonos, que las series temporales no indexan
(spike del 14/10/2026).
"""

from db.schemas import comunes as c

NOMBRE = "eventos_climaticos"
SERIE_TEMPORAL = False

ESQUEMA = {
    "bsonType": "object",
    "required": ["_id", "tipo", "inicio", "fin", "area", "fuente"],
    "additionalProperties": False,
    "properties": {
        "_id": c.OBJECT_ID,
        "tipo": {"enum": ["helada"]},                            # solo heladas: ningún sensor del MVP mide granizo
        "inicio": c.FECHA,
        "fin": c.FECHA,
        "area": c.POLIGONO,                                      # Q4 ($geoIntersects)
        "temperatura_minima_c": c.NUMERO,
        "descripcion": c.TEXTO,
        "fuente": {"enum": ["simulado", "seed"]},
    },
}
