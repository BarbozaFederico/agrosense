"""Crea los índices de agrosense: los geoespaciales de Q3 y Q4 y los de rendimiento medidos (ADR-014, ADR-015).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.indexes.crear_indices

Para otra base, en Git Bash:
    AGROSENSE_BD=agrosense_tests python -m db.indexes.crear_indices

Un índice es una estructura auxiliar que permite a MongoDB encontrar documentos sin leer toda la colección.
Cuesta espacio en disco y hace un poco más lenta cada escritura, por eso solo hay los que una medición
justifica (docs/performance.md):

    2dsphere (posiciones sobre la esfera terrestre). Q3 ($geoNear) NO funciona sin el de `nodos`.
    Rendimiento: bajan los documentos examinados de Q5, Q7, Q8 y Q9.

`lecturas` es una serie temporal: MongoDB ya le crea solo `meta_1_ts_1` y la lee por tiempo. Ese índice se
deja como está (ver el experimento de docs/performance.md); acá solo se agrega uno para Q5.

Se puede repetir: si el índice ya existe, no hace nada.
"""

from pymongo import ASCENDING, DESCENDING, GEOSPHERE

from db.conexion import obtener_base, preparar_consola

# (colección, campo): el campo tiene un Point (nodos) o un Polygon (los otros dos)
INDICES_GEOESPACIALES = [
    ("nodos", "ubicacion"),
    ("parcelas", "geometria"),
    ("eventos_climaticos", "area"),
]

# (colección, claves del índice, consulta que lo justifica). El orden de las claves importa: primero
# las que se comparan con "igual" y después las de rango u orden.
INDICES_RENDIMIENTO = [
    ("lecturas", [("meta.nodo_id", ASCENDING), ("ts", DESCENDING)], "Q5"),      # última lectura de un nodo
    ("riegos", [("parcela_id", ASCENDING), ("inicio", ASCENDING)], "Q7"),       # riegos de una parcela por fecha
    ("alertas", [("tipo", ASCENDING), ("inicio", ASCENDING)], "Q8"),            # alertas de un tipo por fecha
    ("observaciones_fenologicas", [("parcela_id", ASCENDING), ("fecha", DESCENDING)], "Q9"),  # última observación
]


def crear_indices(bd) -> list[str]:
    """Crea los índices geoespaciales y devuelve el nombre de cada uno."""
    return [bd[coleccion].create_index([(campo, GEOSPHERE)]) for coleccion, campo in INDICES_GEOESPACIALES]


def crear_indices_rendimiento(bd) -> list[str]:
    """Crea los índices de rendimiento y devuelve el nombre de cada uno."""
    return [bd[coleccion].create_index(claves) for coleccion, claves, _ in INDICES_RENDIMIENTO]


def main() -> None:
    preparar_consola()
    bd = obtener_base()
    print(f"Base: {bd.name}")
    for (coleccion, campo), nombre in zip(INDICES_GEOESPACIALES, crear_indices(bd)):
        print(f"OK | {coleccion}.{campo} | índice 2dsphere '{nombre}'")
    for (coleccion, _, consulta), nombre in zip(INDICES_RENDIMIENTO, crear_indices_rendimiento(bd)):
        print(f"OK | {coleccion} | índice de rendimiento '{nombre}' (para {consulta})")


if __name__ == "__main__":
    main()
