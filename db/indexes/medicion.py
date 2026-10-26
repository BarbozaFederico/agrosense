"""Herramientas para medir una consulta: documentos examinados, claves examinadas y tiempo (ADR-015).

Qué se mide y por qué:
    docs     Documentos que MongoDB tuvo que LEER para armar la respuesta. Es la cifra principal: no
             depende de qué tan rápida sea la computadora. En una serie temporal cuenta "buckets"
             (grupos de lecturas), no lecturas sueltas.
    claves   Entradas de índice que recorrió. Si es 0 y docs es alto, no usó ningún índice.
    ms       Mediana del tiempo de varias corridas, después de una de calentamiento. Con estos tamaños
             (todo menos de 50 ms) es secundaria.
    planes   Cómo resolvió la lectura: COLLSCAN (lee todo), IXSCAN (usa un índice) o CLUSTERED_IXSCAN
             (el acceso por tiempo propio de las series temporales).

`explain("executionStats")` NO sirve para Q5 y Q9: no muestra lo que pasa adentro de un $lookup, que es
justo donde está el trabajo. Por eso se usa el perfilador de MongoDB (db.setProfilingLevel), que suma todo
lo que leyó cada comando, $lookup incluidos.
"""

import statistics
import time

from pymongo.errors import OperationFailure


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


def tiempo_mediano(funcion, corridas: int = 10) -> float:
    """Mediana, en milisegundos, de `corridas` ejecuciones después de una de calentamiento."""
    funcion()  # calentamiento: carga datos e índices en memoria
    tiempos = []
    for _ in range(corridas):
        inicio = time.perf_counter()
        funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    return statistics.median(tiempos)


def medir(bd, funcion, corridas: int = 10) -> dict:
    """{"docs", "claves", "planes", "ms"} de una consulta; si MongoDB la rechaza, {"error": texto}."""
    try:
        resultado = perfilar(bd, funcion)
        resultado["ms"] = tiempo_mediano(funcion, corridas)
        return resultado
    except OperationFailure as error:
        return {"error": str(error).splitlines()[0][:90]}


def tamanos_de_indices(bd, coleccion: str) -> dict[str, int]:
    """{nombre del índice: bytes que ocupa} de una colección."""
    estadisticas = next(bd[coleccion].aggregate([{"$collStats": {"storageStats": {}}}]))
    return dict(estadisticas["storageStats"]["indexSizes"])
