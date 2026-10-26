"""Esquema de `nodos` (colección común). Campos en docs/modelo-datos.md, sección 3.3.

`estado` es administrativo: si un nodo dejó de reportar se calcula con Q5 (ADR-006).
"""

from db.schemas import comunes as c

NOMBRE = "nodos"
SERIE_TEMPORAL = False

ESQUEMA = {
    "bsonType": "object",
    "required": ["_id", "parcela_id", "finca_id", "ubicacion", "estado", "instalado", "variables"],
    "additionalProperties": False,
    "properties": {
        "_id": c.CODIGO_NODO,  # "N-SR-1-A"
        "parcela_id": c.CODIGO_PARCELA,
        "finca_id": c.CODIGO_FINCA,
        "ubicacion": c.PUNTO,  # Q3 ($geoNear)
        "estado": {"enum": ["activo", "mantenimiento", "baja"]},
        "instalado": c.FECHA,
        # Lista de variables que mide el nodo, sin repetir (uniqueItems).
        "variables": {
            "bsonType": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"enum": ["temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"]},
        },
    },
}
