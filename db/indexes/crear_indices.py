"""Crea los índices geoespaciales que necesitan las consultas Q3 y Q4 (ADR-014).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.indexes.crear_indices

Para otra base, en Git Bash:
    AGROSENSE_BD=agrosense_tests python -m db.indexes.crear_indices

Un índice es una estructura auxiliar que permite a MongoDB encontrar documentos sin leer toda la
colección. Estos son `2dsphere`: indexan posiciones sobre la esfera terrestre. Q3 ($geoNear)
NO funciona sin el índice de `nodos`; los de `parcelas` y `eventos_climaticos` aceleran Q4.

Se puede repetir: si el índice ya existe, no hace nada. Los índices de rendimiento (para medir con
explain() antes y después) se agregan en una tarea aparte, así se puede comparar.
"""

from pymongo import GEOSPHERE

from db.conexion import obtener_base, preparar_consola

# (colección, campo): el campo tiene un Point (nodos) o un Polygon (los otros dos)
INDICES_GEOESPACIALES = [
    ("nodos", "ubicacion"),
    ("parcelas", "geometria"),
    ("eventos_climaticos", "area"),
]


def crear_indices(bd) -> list[str]:
    """Crea los índices y devuelve el nombre de cada uno."""
    return [bd[coleccion].create_index([(campo, GEOSPHERE)]) for coleccion, campo in INDICES_GEOESPACIALES]


def main() -> None:
    preparar_consola()
    bd = obtener_base()
    print(f"Base: {bd.name}")
    for (coleccion, campo), nombre in zip(INDICES_GEOESPACIALES, crear_indices(bd)):
        print(f"OK | {coleccion}.{campo} | índice 2dsphere '{nombre}'")


if __name__ == "__main__":
    main()
