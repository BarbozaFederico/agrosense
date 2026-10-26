"""Carga el seed base: fincas, parcelas, nodos, variedades, configuración y la noche extrema.

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.seeds.cargar

Por defecto usa la base `agrosense` (se crea sola). Para otra base, en Git Bash:
    AGROSENSE_BD=agrosense_tests python -m db.seeds.cargar

Qué hace, en este orden (ADR-010):
    1. Arma todos los documentos en memoria.
    2. Crea las colecciones y sus validadores (repetible, no borra datos).
    3. Revisa las reglas que el esquema no puede expresar (verificar_coherencia y
       verificar_etapas) y valida cada colección con su esquema, SIN guardar.
       Si algo falla, termina acá: no se escribe nada.
    4. Reemplaza el contenido de las colecciones del seed (borra e inserta).
    5. Comprueba la geografía: cada nodo cae dentro de su parcela y cada parcela dentro
       de su finca.

Se puede correr todas las veces que haga falta: el resultado es siempre el mismo. NO toca
`lecturas`, `alertas`, `riegos` ni `observaciones_fenologicas`; de `eventos_climaticos`
reemplaza solo los de fuente "seed".

Quedan fuera por ahora (se cargan al armar el simulador, porque dependen de sus lecturas):
las observaciones fenológicas y las horas exactas de la noche extrema (ADR-009, decisión 8).
"""

import sys

from pymongo.database import Database

from db.conexion import obtener_base, preparar_consola
from db.departamentos import clave_departamento
from db.schemas import ESQUEMAS, configuracion as esquema_configuracion, lecturas
from db.schemas.crear import crear_colecciones
from db.schemas.validar import validar_documentos
from db.seeds import configuracion, eventos_climaticos, fincas, nodos, parcelas, variedades

# Orden de carga: primero la configuración y los datos de los que dependen los demás.
MODULOS = [configuracion, variedades, fincas, parcelas, nodos, eventos_climaticos]

ESQUEMA_DE = {modulo.NOMBRE: modulo.ESQUEMA for modulo in ESQUEMAS}


def armar_documentos(umbrales=None) -> dict[str, list[dict]]:
    """Todos los documentos del seed, por colección. `umbrales` es solo para pruebas."""
    docs = {}
    for modulo in MODULOS:
        docs[modulo.NOMBRE] = modulo.documentos(umbrales) if modulo is configuracion else modulo.documentos()
    return docs


def verificar_reglas(docs: dict[str, list[dict]]) -> list[str]:
    """Reglas que el esquema no puede expresar porque comparan campos o documentos."""
    errores = []
    departamento_de_finca = {f["_id"]: clave_departamento(f["departamento"]) for f in docs["fincas"]}
    imposible = lecturas.ESQUEMA["properties"]["temperatura_c"]["minimum"]  # hoy -40, provisional
    errores += esquema_configuracion.verificar_coherencia(docs["configuracion"][0], departamento_de_finca, imposible)
    for variedad in docs["variedades"]:
        errores += [f"variedad {variedad['_id']}: {e}" for e in variedades.verificar_etapas(variedad["etapas"])]

    # Referencias entre colecciones: cada parcela, nodo y variedad apunta a algo que existe.
    fincas_ids = {f["_id"] for f in docs["fincas"]}
    parcelas_ids = {p["_id"] for p in docs["parcelas"]}
    variedades_ids = {v["_id"] for v in docs["variedades"]}
    for p in docs["parcelas"]:
        if p["finca_id"] not in fincas_ids:
            errores.append(f"{p['_id']}: finca_id {p['finca_id']} no existe")
        if p["variedad_id"] not in variedades_ids:
            errores.append(f"{p['_id']}: variedad_id {p['variedad_id']} no existe")
    finca_de_parcela = {p["_id"]: p["finca_id"] for p in docs["parcelas"]}
    for n in docs["nodos"]:
        if n["parcela_id"] not in parcelas_ids:
            errores.append(f"{n['_id']}: parcela_id {n['parcela_id']} no existe")
        elif finca_de_parcela[n["parcela_id"]] != n["finca_id"]:
            errores.append(f"{n['_id']}: finca_id {n['finca_id']} no coincide con la de su parcela")
    return errores


def validar_todo(bd: Database, docs: dict[str, list[dict]]) -> list[str]:
    """Valida cada colección con su esquema sin guardar. Devuelve los errores."""
    errores = []
    for nombre, lista in docs.items():
        validos, invalidos = validar_documentos(bd, ESQUEMA_DE[nombre], lista)
        print(f"  {nombre}: {len(validos)} válidos, {len(invalidos)} inválidos")
        errores += [f"{nombre}: documento inválido {d.get('_id', '(sin _id)')}" for d in invalidos]
    return errores


def reemplazar(bd: Database, docs: dict[str, list[dict]]) -> None:
    """Borra el contenido del seed en cada colección y lo vuelve a insertar."""
    for nombre, lista in docs.items():
        # Los eventos de otras fuentes (por ejemplo, de una simulación) no se tocan.
        filtro = {"fuente": "seed"} if nombre == "eventos_climaticos" else {}
        borrados = bd[nombre].delete_many(filtro).deleted_count
        bd[nombre].insert_many(lista)
        print(f"  {nombre}: {borrados} borrados, {len(lista)} insertados")


def verificar_geografia(bd: Database) -> list[str]:
    """Cada nodo dentro de su parcela y cada parcela dentro de su finca (le pregunta a MongoDB)."""
    errores = []
    for nodo in bd.nodos.find():
        dentro = bd.parcelas.count_documents(
            {"_id": nodo["parcela_id"], "geometria": {"$geoIntersects": {"$geometry": nodo["ubicacion"]}}}
        )
        if dentro != 1:
            errores.append(f"{nodo['_id']} no está dentro de {nodo['parcela_id']}")
    for finca in bd.fincas.find():
        # $geoWithin: parcelas cuyo polígono queda entero dentro del polígono de la finca.
        dentro = {
            p["_id"]
            for p in bd.parcelas.find(
                {"finca_id": finca["_id"], "geometria": {"$geoWithin": {"$geometry": finca["geometria"]}}}, {"_id": 1}
            )
        }
        todas = {p["_id"] for p in bd.parcelas.find({"finca_id": finca["_id"]}, {"_id": 1})}
        errores += [f"{p} no está dentro de {finca['_id']}" for p in sorted(todas - dentro)]
    return errores


def cargar(bd: Database, umbrales=None) -> list[str]:
    """Corre los 5 pasos. Devuelve los errores (lista vacía si salió todo bien)."""
    # Primero se arman los documentos: si falta un dato (los umbrales de riego), se frena
    # antes de tocar la base.
    print("1) Armado de documentos")
    docs = armar_documentos(umbrales)

    print("2) Colecciones y validadores")
    crear_colecciones(bd)

    print("3) Reglas y validación (sin guardar)")
    errores = verificar_reglas(docs) + validar_todo(bd, docs)
    if errores:
        return errores

    print("4) Carga")
    reemplazar(bd, docs)

    print("5) Geografía")
    errores = verificar_geografia(bd)
    print("  nodos en su parcela y parcelas en su finca: " + ("OK" if not errores else "FALLA"))
    return errores


def main() -> None:
    preparar_consola()
    bd = obtener_base()
    print(f"Versión del servidor: {bd.client.server_info()['version']} | base: {bd.name}")
    try:
        errores = cargar(bd)
    except RuntimeError as error:
        print(f"\nNO SE CARGÓ NADA: {error}")
        sys.exit(1)
    if errores:
        print("\nERRORES:")
        for error in errores:
            print(f"  - {error}")
        sys.exit(1)
    print("\nSeed cargado correctamente.")


if __name__ == "__main__":
    main()
