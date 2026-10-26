"""Esquemas $jsonSchema de las 10 colecciones de agrosense.

Cada módulo (fincas.py, lecturas.py, ...) define:
    NOMBRE          nombre de la colección
    SERIE_TEMPORAL  True solo para `lecturas`
    ESQUEMA         el $jsonSchema (un diccionario de Python)

ESQUEMAS es la lista de esos módulos, en el orden en que se crean: primero la
configuración y los datos fijos, después los eventos.
"""

from db.schemas import (
    alertas,
    configuracion,
    eventos_climaticos,
    fincas,
    lecturas,
    nodos,
    observaciones_fenologicas,
    parcelas,
    riegos,
    variedades,
)

ESQUEMAS = [
    configuracion,
    variedades,
    fincas,
    parcelas,
    nodos,
    lecturas,
    alertas,
    riegos,
    eventos_climaticos,
    observaciones_fenologicas,
]
