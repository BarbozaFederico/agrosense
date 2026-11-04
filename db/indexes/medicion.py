"""Herramientas de las pruebas de índices: lo que MongoDB leyó en una consulta y lo que ocupa cada índice (ADR-015).

`perfilar` usa el perfilador de MongoDB (db.setProfilingLevel), que suma todo lo que leyó cada comando, $lookup
incluidos (el `explain` no muestra lo de adentro de un $lookup). Devuelve:
    docs     Documentos que MongoDB tuvo que LEER. En una serie temporal cuenta "buckets", no lecturas sueltas.
    claves   Entradas de índice que recorrió. Si es 0 y docs es alto, no usó ningún índice.
    planes   Cómo resolvió la lectura (COLLSCAN, IXSCAN, CLUSTERED_IXSCAN...).

La tabla de `medir_indices.py` usa otra cosa, más simple: `totalDocsExamined` del explain de una búsqueda.
"""


def perfilar(bd, funcion) -> dict:
    """Corre `funcion` una vez con el perfilador encendido y suma lo que MongoDB leyó."""
    bd.command("profile", 0)
    bd.system.profile.drop()
    bd.command("profile", 2)  # nivel 2: registra TODAS las operaciones
    try:
        funcion()
    finally:
        bd.command("profile", 0)
    operaciones = [o for o in bd.system.profile.find() if not o.get("ns", "").endswith("system.profile")]
    return {
        "docs": sum(o.get("docsExamined", 0) for o in operaciones),
        "claves": sum(o.get("keysExamined", 0) for o in operaciones),
        "planes": sorted({o["planSummary"] for o in operaciones if o.get("planSummary")}),
    }


def tamanos_de_indices(bd, coleccion: str) -> dict[str, int]:
    """{nombre del índice: bytes que ocupa} de una colección."""
    estadisticas = next(bd[coleccion].aggregate([{"$collStats": {"storageStats": {}}}]))
    return dict(estadisticas["storageStats"]["indexSizes"])
