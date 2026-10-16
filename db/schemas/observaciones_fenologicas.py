"""Esquema de `observaciones_fenologicas` (colección común). Campos en docs/modelo-datos.md, sección 3.8.

Si existe una observación, manda sobre la estimación por grados-día (ADR-004).
"""

from db.schemas import comunes as c

NOMBRE = "observaciones_fenologicas"
SERIE_TEMPORAL = False

ESQUEMA = {
    "bsonType": "object",
    "required": ["_id", "parcela_id", "fecha", "etapa_bbch", "observador", "fuente"],
    "additionalProperties": False,
    "properties": {
        "_id": c.OBJECT_ID,
        "parcela_id": c.CODIGO_PARCELA,
        "fecha": c.FECHA,
        "etapa_bbch": c.ETAPA_BBCH,
        "observador": {"enum": ["tecnico", "encargado"]},        # un rol, no un nombre (repo público)
        "notas": c.TEXTO,
        "fuente": {"enum": ["seed"]},                            # solo precargadas (ADR-004)
    },
}
