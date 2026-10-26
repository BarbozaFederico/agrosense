"""Mide las consultas Q1 a Q10 antes y después de crear los índices (RNF-01, ADR-015).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.indexes.medir_indices
    python -m db.indexes.medir_indices --corridas 20 --cargar      # vuelve a generar los datos antes

Usa la base de PRUEBA `agrosense_tests` (si está vacía, carga el seed y la temporada ahí). No toca la base
real `agrosense`: este script BORRA y CREA índices, y no corresponde hacerlo sobre la base real.

Qué hace, en este orden:
    1. Borra los índices de este proyecto (los geoespaciales y los de rendimiento).
    2. ANTES: mide las 10 consultas.
    3. Crea los índices (db/indexes/crear_indices.py).
    4. DESPUÉS: vuelve a medir las 10 consultas.
    5. Experimento: borra el índice automático de `lecturas` (meta_1_ts_1), mide Q1, Q5, Q6 y Q9 sin él y lo
       vuelve a crear. En la base real ese índice nunca se borra.
    6. Mide cuánto ocupa cada índice.
Imprime las tablas en Markdown, listas para docs/performance.md. Al terminar deja los índices creados.
"""

import argparse
import contextlib
import io
import os
import platform
from datetime import date

from pymongo import ASCENDING, DESCENDING

from db.conexion import obtener_base, preparar_consola
from db.indexes import medicion
from db.indexes.crear_indices import (
    INDICES_GEOESPACIALES,
    INDICES_RENDIMIENTO,
    crear_indices,
    crear_indices_rendimiento,
)
from db.queries import (
    comun,
    q1_horas_bajo_cero as q1,
    q2_minima_bajo_umbral as q2,
    q3_nodos_cercanos as q3,
    q4_parcelas_en_evento as q4,
    q5_nodos_sin_reportar as q5,
    q6_humedad_suelo_horaria as q6,
    q7_litros_por_semana as q7,
    q8_heladas_por_departamento as q8,
    q9_etapa_por_grados_dia as q9,
    q10_riesgo_de_helada as q10,
)

BASE_DE_PRUEBA = "agrosense_tests"
INDICE_AUTOMATICO = "meta_1_ts_1"
FECHA = date(2026, 10, 5)

# id, qué mide, colección del índice que le sirve (o "-" si no necesita uno nuevo)
CONSULTAS = [
    ("Q1", "horas bajo cero de una noche", "-"),
    ("Q2", "parcelas bajo el umbral", "observaciones (por Q9)"),
    ("Q3", "nodos más cercanos", "nodos 2dsphere"),
    ("Q4", "parcelas dentro de un evento", "parcelas 2dsphere"),
    ("Q5", "nodos sin reportar", "lecturas"),
    ("Q6", "humedad de suelo por hora", "-"),
    ("Q7", "litros por parcela y semana", "riegos"),
    ("Q8", "heladas por departamento", "alertas"),
    ("Q9", "etapa por grados-día", "observaciones"),
    ("Q10", "índice de riesgo de helada", "observaciones (por Q9)"),
]


def funciones(bd) -> dict:
    """Cada consulta con los parámetros de las pruebas (la noche del 5/10 y el 'ahora' por defecto)."""
    return {
        "Q1": lambda: q1.consultar(bd, FECHA),
        "Q2": lambda: q2.consultar(bd, FECHA),
        "Q3": lambda: q3.consultar(bd),
        "Q4": lambda: q4.consultar(bd),
        "Q5": lambda: q5.consultar(bd),
        "Q6": lambda: q6.consultar(bd),
        "Q7": lambda: q7.consultar(bd, "P-SR-1"),
        "Q8": lambda: q8.consultar(bd),
        "Q9": lambda: q9.consultar(bd, FECHA),
        "Q10": lambda: q10.consultar(bd, FECHA),
    }


def nombre_de_indice(claves) -> str:
    """El nombre que MongoDB le da a un índice: campo_orden por cada clave."""
    return "_".join(f"{campo}_{orden}" for campo, orden in claves)


def quitar_indices(bd) -> None:
    """Borra los índices de este proyecto (no toca el automático de las series temporales)."""
    existentes = {
        coleccion: {i["name"] for i in bd[coleccion].list_indexes()}
        for coleccion in {c for c, *_ in INDICES_GEOESPACIALES + INDICES_RENDIMIENTO}
    }
    for coleccion, campo in INDICES_GEOESPACIALES:
        nombre = f"{campo}_2dsphere"
        if nombre in existentes[coleccion]:
            bd[coleccion].drop_index(nombre)
    for coleccion, claves, _ in INDICES_RENDIMIENTO:
        nombre = nombre_de_indice(claves)
        if nombre in existentes[coleccion]:
            bd[coleccion].drop_index(nombre)


def medir_todas(bd, ids: list[str] | None, corridas: int) -> dict:
    fns = funciones(bd)
    return {i: medicion.medir(bd, fns[i], corridas) for i in (ids or list(fns))}


# --------------------------------------------------------------------------- tablas


def _plan(m: dict) -> str:
    if "error" in m:
        return "falla"
    planes = [p.split(" {")[0] for p in m["planes"]]
    return " + ".join(dict.fromkeys(planes)) or "-"


def _flecha(a, b, formato) -> str:
    return formato(a) if a == b else f"{formato(a)} → {formato(b)}"


def _cifras(m: dict, campo: str, formato) -> str:
    return "falla" if "error" in m else formato(m[campo])


def tabla_resultados(antes: dict, despues: dict) -> str:
    filas = [
        "| Consulta | Qué responde | Índice que le sirve | Documentos examinados | Claves de índice | Tiempo (ms) | Plan |",
        "|---|---|---|---|---|---|---|",
    ]
    entero, un_decimal = (lambda v: f"{v:,}".replace(",", ".")), (lambda v: f"{v:.1f}")
    for i, que, indice in CONSULTAS:
        a, d = antes[i], despues[i]
        if "error" in a:
            docs = f"falla → {_cifras(d, 'docs', entero)}"
            claves = f"falla → {_cifras(d, 'claves', entero)}"
            ms = f"falla → {_cifras(d, 'ms', un_decimal)}"
        else:
            docs, claves = _flecha(a["docs"], d["docs"], entero), _flecha(a["claves"], d["claves"], entero)
            ms = f"{un_decimal(a['ms'])} → {un_decimal(d['ms'])}"
        plan = _plan(a) if _plan(a) == _plan(d) else f"{_plan(a)} → {_plan(d)}"
        filas.append(f"| {i} | {que} | {indice} | {docs} | {claves} | {ms} | {plan} |")
    return "\n".join(filas)


def tabla_experimento(con: dict, sin: dict) -> str:
    filas = ["| Consulta | Documentos examinados con / sin `meta_1_ts_1` | Tiempo (ms) con / sin |", "|---|---|---|"]
    for i in sorted(con, key=lambda x: int(x[1:])):
        filas.append(f"| {i} | {con[i]['docs']} / {sin[i]['docs']} | {con[i]['ms']:.1f} / {sin[i]['ms']:.1f} |")
    return "\n".join(filas)


def tabla_tamanos(bd) -> str:
    filas = ["| Colección | Índice | Tamaño | Para |", "|---|---|---|---|"]
    for coleccion, campo in INDICES_GEOESPACIALES:
        t = medicion.tamanos_de_indices(bd, coleccion)[f"{campo}_2dsphere"]
        filas.append(
            f"| {coleccion} | `{campo}_2dsphere` | {t / 1024:.1f} KB | {'Q3' if coleccion == 'nodos' else 'Q4'} |"
        )
    for coleccion, claves, consulta in INDICES_RENDIMIENTO:
        t = medicion.tamanos_de_indices(bd, coleccion)[nombre_de_indice(claves)]
        filas.append(f"| {coleccion} | `{nombre_de_indice(claves)}` | {t / 1024:.1f} KB | {consulta} |")
    auto = medicion.tamanos_de_indices(bd, "lecturas")[INDICE_AUTOMATICO]
    filas.append(f"| lecturas | `{INDICE_AUTOMATICO}` (automático) | {auto / 1024:.1f} KB | referencia |")
    return "\n".join(filas)


# --------------------------------------------------------------------------- script


def main() -> None:
    preparar_consola()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corridas", type=int, default=10, help="corridas para la mediana del tiempo (por defecto 10)")
    p.add_argument("--cargar", action="store_true", help="vuelve a cargar el seed y la temporada antes de medir")
    a = p.parse_args()

    bd = obtener_base(BASE_DE_PRUEBA)
    if a.cargar or bd.lecturas.estimated_document_count() == 0:
        from db.seeds import cargar as cargar_seed
        from simulator import generar

        print("Cargando el seed y la temporada en la base de prueba...")
        with contextlib.redirect_stdout(io.StringIO()):
            cargar_seed.cargar(bd)
            generar.escribir(bd, generar.simular(generar.cargar_contexto(bd)))

    version = bd.client.server_info()["version"]
    print(f"## Mediciones ({date.today():%d/%m/%Y})\n")
    print(
        f"- Base: `{bd.name}` · MongoDB {version} · {bd.lecturas.estimated_document_count():,} lecturas".replace(
            ",", "."
        )
    )
    print(f"- Equipo: {platform.platform()}, {os.cpu_count()} núcleos lógicos · Python {platform.python_version()}")
    print(f"- Tiempo: mediana de {a.corridas} corridas después de una de calentamiento\n")

    quitar_indices(bd)
    antes = medir_todas(bd, None, a.corridas)
    crear_indices(bd)
    crear_indices_rendimiento(bd)
    despues = medir_todas(bd, None, a.corridas)
    print("### Antes y después de crear los índices\n")
    print(tabla_resultados(antes, despues))

    ids_lecturas = ["Q1", "Q5", "Q6", "Q9"]
    con = {i: despues[i] for i in ids_lecturas}
    bd.lecturas.drop_index(INDICE_AUTOMATICO)
    try:
        sin = medir_todas(bd, ids_lecturas, a.corridas)
    finally:
        bd.lecturas.create_index([("meta", ASCENDING), ("ts", ASCENDING)], name=INDICE_AUTOMATICO)
    print("\n### Experimento: ¿hace falta el índice automático de `lecturas`?\n")
    print(tabla_experimento(con, sin))
    print("\n### Costo: lo que ocupa cada índice\n")
    print(tabla_tamanos(bd))


if __name__ == "__main__":
    main()
