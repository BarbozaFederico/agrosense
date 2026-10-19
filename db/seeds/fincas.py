"""Datos de `fincas` (3 fincas ficticias). Esquema: db/schemas/fincas.py.

Sistema de riego y suelo por finca: ADR-005 (decisiones 4 y 5).
Altitud: la de la estación de referencia de cada zona, aproximada (supuesto adoptado, ADR-012):
    San Rafael Aero (SMN) 751 m · San Martín (SMN) 653 m · El Peral (DACC) 1.300 m
    (docs/investigacion/verificacion-fuentes.md).
"""

from db.seeds.ubicaciones import geometria_finca

NOMBRE = "fincas"

DATOS = [
    # _id, nombre, departamento, oasis, altitud_m, sistema_riego, tipo_suelo
    ("F-SR", "Finca Los Álamos", "San Rafael", "Sur", 751, "surco", "franco"),
    ("F-SM", "Finca El Algarrobo", "San Martín", "Este", 653, "surco", "franco_arenoso"),
    ("F-TU", "Finca Los Cipreses", "Tupungato", "Valle de Uco", 1300, "goteo", "pedregoso"),
]


def documentos() -> list[dict]:
    return [
        {"_id": id_, "nombre": nombre, "departamento": departamento, "oasis": oasis,
         "altitud_m": altitud, "geometria": geometria_finca(id_),
         "sistema_riego": riego, "tipo_suelo": suelo, "ficticia": True}
        for id_, nombre, departamento, oasis, altitud, riego, suelo in DATOS
    ]
