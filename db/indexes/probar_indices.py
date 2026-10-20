"""Prueba de los índices.

Pregunta: ¿los índices existen, los usa MongoDB, mejoran lo que dicen mejorar y NO cambian ninguna respuesta?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.indexes.probar_indices

Usa la base de PRUEBA `agrosense_tests` (si está vacía, carga el seed y la temporada ahí). Borra y vuelve a
crear los índices de esa base. No toca la base real `agrosense`. Tarda unos segundos.
"""

import contextlib
import io
import json
import sys

from bson import json_util

from db.conexion import obtener_base, preparar_consola
from db.indexes import medicion
from db.indexes.crear_indices import (INDICES_GEOESPACIALES, INDICES_RENDIMIENTO, crear_indices,
                                      crear_indices_rendimiento)
from db.indexes.medir_indices import INDICE_AUTOMATICO, BASE_DE_PRUEBA, funciones, nombre_de_indice, quitar_indices
from db.schemas.probar_esquemas import Resumen


def normalizar(resultado) -> str:
    """El resultado de una consulta como texto comparable (sin depender del orden de los campos)."""
    return json.dumps(json.loads(json_util.dumps(resultado)), sort_keys=True)


def usa_indice(plan, nombre: str) -> bool:
    return f'"indexName": "{nombre}"' in json.dumps(plan, default=str)


def main() -> None:
    preparar_consola()
    r = Resumen()
    bd = obtener_base(BASE_DE_PRUEBA)
    if bd.lecturas.estimated_document_count() == 0:
        from db.seeds import cargar as cargar_seed
        from simulator import generar
        with contextlib.redirect_stdout(io.StringIO()):
            cargar_seed.cargar(bd)
            generar.escribir(bd, generar.simular(generar.cargar_contexto(bd)))
    print(f"Base de prueba: {bd.name} (los índices se borran y se crean acá; la base real no se toca)")
    fns = funciones(bd)

    print("--- Sin índices de rendimiento: resultados y mediciones de referencia")
    quitar_indices(bd)
    sin_indices = {i: normalizar(fns[i]()) for i in ("Q2", "Q5", "Q7", "Q8", "Q9", "Q10")}
    antes = {i: medicion.perfilar(bd, fns[i]) for i in ("Q5", "Q7", "Q8", "Q9")}
    r.chequear(antes["Q7"]["docs"] >= 500 and "COLLSCAN" in antes["Q7"]["planes"][0],
               f"antes | Q7 lee la colección entera: {antes['Q7']['docs']} documentos, plan {antes['Q7']['planes']}")
    r.chequear(antes["Q5"]["docs"] > 4000 and antes["Q5"]["claves"] <= 1,
               f"antes | Q5 no usa ningún índice dentro del $lookup: {antes['Q5']['docs']} documentos, {antes['Q5']['claves']} claves")

    print("--- Crear los índices")
    nombres = crear_indices(bd) + crear_indices_rendimiento(bd)
    esperados = [f"{campo}_2dsphere" for _, campo in INDICES_GEOESPACIALES] + \
                [nombre_de_indice(claves) for _, claves, _ in INDICES_RENDIMIENTO]
    r.chequear(nombres == esperados, f"crear | se crearon los {len(nombres)} índices con los nombres esperados")
    otra_vez = crear_indices(bd) + crear_indices_rendimiento(bd)
    r.chequear(otra_vez == nombres, "crear | repetir no falla ni duplica índices (es idempotente)")
    r.chequear(INDICE_AUTOMATICO in {i["name"] for i in bd.lecturas.list_indexes()},
               f"crear | el índice automático de la serie temporal ({INDICE_AUTOMATICO}) sigue en lecturas")

    print("--- MongoDB los usa")
    planes = {
        "riegos": bd.riegos.find({"parcela_id": "P-SR-1"}).explain()["queryPlanner"]["winningPlan"],
        "alertas": bd.alertas.find({"tipo": "helada"}).explain()["queryPlanner"]["winningPlan"],
        "observaciones_fenologicas": bd.observaciones_fenologicas.find({"parcela_id": "P-SR-1"}).sort("fecha", -1)
                                       .limit(1).explain()["queryPlanner"]["winningPlan"],
    }
    for (coleccion, claves, consulta) in INDICES_RENDIMIENTO[1:]:
        r.chequear(usa_indice(planes[coleccion], nombre_de_indice(claves)),
                   f"plan | {consulta}: la búsqueda en {coleccion} usa el índice {nombre_de_indice(claves)} (IXSCAN)")

    print("--- Mejoran lo que dicen mejorar")
    despues = {i: medicion.perfilar(bd, fns[i]) for i in ("Q5", "Q7", "Q8", "Q9")}
    for i, minimo in (("Q5", 5), ("Q7", 5)):
        r.chequear(despues[i]["docs"] * minimo <= antes[i]["docs"] and despues[i]["claves"] > 0,
                   f"mejora | {i}: documentos examinados {antes[i]['docs']} → {despues[i]['docs']} "
                   f"(al menos {minimo} veces menos), claves {antes[i]['claves']} → {despues[i]['claves']}")
    for i in ("Q8", "Q9"):
        r.chequear(despues[i]["docs"] < antes[i]["docs"],
                   f"mejora | {i}: documentos examinados {antes[i]['docs']} → {despues[i]['docs']}")

    print("--- No cambian ninguna respuesta")
    for i, texto in sin_indices.items():
        r.chequear(normalizar(fns[i]()) == texto, f"resultado | {i} devuelve exactamente lo mismo con y sin índices")

    print("--- Costo")
    tamanos = {nombre: tam for c in ("lecturas", "riegos", "alertas", "observaciones_fenologicas")
               for nombre, tam in medicion.tamanos_de_indices(bd, c).items()}
    r.chequear(all(tamanos[nombre_de_indice(claves)] > 0 for _, claves, _ in INDICES_RENDIMIENTO),
               "costo | se puede medir lo que ocupa cada índice de rendimiento: " +
               ", ".join(f"{nombre_de_indice(c)} {tamanos[nombre_de_indice(c)] / 1024:.0f} KB" for _, c, _ in INDICES_RENDIMIENTO))

    print("---")
    print(f"RESULTADO: todos los casos dieron lo esperado ({r.total} casos)" if r.fallas == 0
          else f"RESULTADO: {r.fallas} de {r.total} casos NO dieron lo esperado")
    if r.fallas:
        sys.exit(1)


if __name__ == "__main__":
    main()
