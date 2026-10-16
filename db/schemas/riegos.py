"""Esquema de `riegos` (colección común). Campos en docs/modelo-datos.md, sección 3.6.

Riego mixto (ADR-004): por turno o por alerta. Agua en mm y en litros (ADR-006).
"""

from db.schemas import comunes as c

NOMBRE = "riegos"
SERIE_TEMPORAL = False

ESQUEMA = {
    "bsonType": "object",
    "required": ["_id", "parcela_id", "inicio", "fin", "sistema", "origen",
                 "lamina_mm", "litros", "fuente"],
    "additionalProperties": False,
    "properties": {
        "_id": c.OBJECT_ID,
        "parcela_id": c.CODIGO_PARCELA,
        "inicio": c.FECHA,
        "fin": c.FECHA,
        "sistema": {"enum": ["surco", "goteo"]},
        "origen": {"enum": ["turno", "alerta"]},
        "alerta_id": c.OBJECT_ID,                                # solo si origen es "alerta"
        "lamina_mm": c.POSITIVO,                                 # lo que informan las fuentes
        "litros": c.POSITIVO,                                    # lamina_mm × superficie_ha × 10.000 (Q7)
        "fuente": c.FUENTE_SIMULADA,
        "escenario_id": c.TEXTO,
    },
    # Regla: un riego originado por una alerta tiene que decir qué alerta fue.
    "anyOf": [
        {"properties": {"origen": {"enum": ["turno"]}}},
        {"properties": {"origen": {"enum": ["alerta"]}}, "required": ["alerta_id"]},
    ],
}
