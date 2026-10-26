"""Datos de `parcelas` (6, dos por finca). Esquema: db/schemas/parcelas.py.

Todas son de Malbec (ADR-004). Superficie (2 ha), conducción (espaldero) y densidad
(4.000 plantas/ha) son SUPUESTOS: el informe del INV no trae conducción ni densidad
(docs/investigacion/verificacion-fuentes.md, sección 2).
"""

from db.seeds.ubicaciones import PARCELAS_DE_FINCA, SUPERFICIE_HA, geometria_parcela

NOMBRE = "parcelas"

DENSIDAD_PLANTAS_HA = 4000


def documentos() -> list[dict]:
    docs = []
    for finca_id, parcelas in PARCELAS_DE_FINCA.items():
        for parcela_id in parcelas:
            numero = parcela_id.split("-")[2]
            docs.append(
                {
                    "_id": parcela_id,
                    "finca_id": finca_id,
                    "nombre": f"Cuartel {numero}",
                    "variedad_id": "malbec",
                    "superficie_ha": SUPERFICIE_HA,
                    "geometria": geometria_parcela(parcela_id),
                    "conduccion": "espaldero",
                    "densidad_plantas_ha": DENSIDAD_PLANTAS_HA,
                }
            )
    return docs
