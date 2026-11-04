"""Crea los 4 índices de agrosense: dos geoespaciales (Q3 y Q4) y dos de rendimiento (Q5 y Q7) (ADR-014 y ADR-022).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.indexes.crear_indices

Para otra base, en Git Bash:
    AGROSENSE_BD=agrosense_tests python -m db.indexes.crear_indices

Un índice es una estructura auxiliar que permite a MongoDB encontrar documentos sin leer toda la colección.
Cuesta espacio en disco y hace un poco más lenta cada escritura, por eso solo hay los que una medición
justifica (docs/performance.md):

    nodos.ubicacion       2dsphere  Q3: `$geoNear` NO funciona sin él (es el único obligatorio).
    parcelas.geometria    2dsphere  Q4: funciona igual sin él; se deja porque es el par de Q3 (geoespacial).
    lecturas              {meta.nodo_id, ts}   Q5: baja de 5.053 a 433 los documentos examinados.
    riegos                {parcela_id, inicio} Q7: pasa de leer toda la colección a leer solo los de la parcela.

Se midieron otros tres y se descartaron (INDICES_DESCARTADOS, ADR-022): este script no los crea y, si una base
los tiene porque se hizo antes de ese ADR, los borra.

`lecturas` es una serie temporal: MongoDB ya le crea solo `meta_1_ts_1` y la lee por tiempo. Ese índice se
deja como está (ver el experimento de docs/performance.md); acá solo se agrega uno para Q5.

Se puede repetir: si el índice ya existe, no hace nada.
"""

from pymongo import ASCENDING, DESCENDING, GEOSPHERE

from db.conexion import obtener_base, preparar_consola

# (colección, campo): el campo tiene un Point (nodos) o un Polygon (parcelas)
INDICES_GEOESPACIALES = [
    ("nodos", "ubicacion"),
    ("parcelas", "geometria"),
]

# (colección, claves del índice, consulta que lo justifica). El orden de las claves importa: primero
# las que se comparan con "igual" y después las de rango u orden.
INDICES_RENDIMIENTO = [
    ("lecturas", [("meta.nodo_id", ASCENDING), ("ts", DESCENDING)], "Q5"),  # última lectura de un nodo
    ("riegos", [("parcela_id", ASCENDING), ("inicio", ASCENDING)], "Q7"),  # riegos de una parcela por fecha
]

# Candidatos que se midieron y NO valen su costo (ADR-022, docs/performance.md). Nunca se crean:
# medir_indices.py los crea un momento para comparar y los borra.
# (colección, claves, consultas que podrían mejorar)
INDICES_DESCARTADOS = [
    ("eventos_climaticos", [("area", GEOSPHERE)], ["Q4"]),  # ninguna consulta lo usa: Q4 busca sobre parcelas
    ("alertas", [("tipo", ASCENDING), ("inicio", ASCENDING)], ["Q8"]),  # 35 documentos; tipo tiene 2 valores
    ("observaciones_fenologicas", [("parcela_id", ASCENDING), ("fecha", DESCENDING)], ["Q9", "Q2", "Q10"]),
]


def nombre_de_indice(claves) -> str:
    """El nombre que MongoDB le da a un índice: campo_orden por cada clave."""
    return "_".join(f"{campo}_{orden}" for campo, orden in claves)


def crear_indices(bd) -> list[str]:
    """Crea los índices geoespaciales y devuelve el nombre de cada uno."""
    return [bd[coleccion].create_index([(campo, GEOSPHERE)]) for coleccion, campo in INDICES_GEOESPACIALES]


def crear_indices_rendimiento(bd) -> list[str]:
    """Crea los índices de rendimiento y devuelve el nombre de cada uno."""
    return [bd[coleccion].create_index(claves) for coleccion, claves, _ in INDICES_RENDIMIENTO]


def quitar_indices_descartados(bd) -> list[str]:
    """Borra los índices descartados si la base los tiene (por ejemplo, una creada antes del ADR-022)."""
    borrados = []
    for coleccion, claves, _ in INDICES_DESCARTADOS:
        nombre = nombre_de_indice(claves)
        if nombre in {i["name"] for i in bd[coleccion].list_indexes()}:
            bd[coleccion].drop_index(nombre)
            borrados.append(f"{coleccion}.{nombre}")
    return borrados


def main() -> None:
    preparar_consola()
    bd = obtener_base()
    print(f"Base: {bd.name}")
    for (coleccion, campo), nombre in zip(INDICES_GEOESPACIALES, crear_indices(bd)):
        print(f"OK | {coleccion}.{campo} | índice 2dsphere '{nombre}'")
    for (coleccion, _, consulta), nombre in zip(INDICES_RENDIMIENTO, crear_indices_rendimiento(bd)):
        print(f"OK | {coleccion} | índice de rendimiento '{nombre}' (para {consulta})")
    for borrado in quitar_indices_descartados(bd):
        print(f"BORRADO | {borrado} | índice descartado (ADR-022)")


if __name__ == "__main__":
    main()
