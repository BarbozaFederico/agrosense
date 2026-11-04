"""Mide las consultas Q1 a Q10 antes y después de crear los índices (RNF-01, ADR-015).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.indexes.medir_indices
    python -m db.indexes.medir_indices --corridas 20 --cargar      # vuelve a generar los datos antes

Usa la base de PRUEBA `agrosense_tests` (si está vacía, carga el seed y la temporada ahí). No toca la base
real `agrosense`: este script BORRA y CREA índices, y no corresponde hacerlo sobre la base real.

Qué hace, en este orden:
    1. Borra los índices de este proyecto (los 4 elegidos y los 3 descartados).
    2. ANTES: mide las 10 consultas.
    3. Crea los 4 índices elegidos (db/indexes/crear_indices.py).
    4. DESPUÉS: vuelve a medir las 10 consultas.
    5. Candidatos descartados (ADR-022): crea cada uno por separado, mide las consultas que podría mejorar y lo
       borra. Sirve de evidencia de por qué no se crean.
    6. Experimento: borra el índice automático de `lecturas` (meta_1_ts_1), mide Q1, Q5, Q6 y Q9 sin él y lo
       vuelve a crear. En la base real ese índice nunca se borra.
    7. Mide cuánto ocupa cada índice.
Imprime las tablas en Markdown, listas para docs/performance.md. Al terminar deja los 4 índices elegidos.
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
    INDICES_DESCARTADOS,
    INDICES_GEOESPACIALES,
    INDICES_RENDIMIENTO,
    crear_indices,
    crear_indices_rendimiento,
    nombre_de_indice,
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
    ("Q2", "parcelas bajo el umbral", "-"),
    ("Q3", "nodos más cercanos", "nodos 2dsphere"),
    ("Q4", "parcelas dentro de un evento", "parcelas 2dsphere (opcional)"),
    ("Q5", "nodos sin reportar", "lecturas"),
    ("Q6", "humedad de suelo por hora", "-"),
    ("Q7", "litros por parcela y semana", "riegos"),
    ("Q8", "heladas por departamento", "-"),
    ("Q9", "etapa por grados-día", "-"),
    ("Q10", "índice de riesgo de helada", "-"),
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


def quitar_indices(bd) -> None:
    """Borra los índices de este proyecto, elegidos y descartados (no toca el automático de las series temporales)."""
    todos = (
        [(c, f"{campo}_2dsphere") for c, campo in INDICES_GEOESPACIALES]
        + [(c, nombre_de_indice(claves)) for c, claves, _ in INDICES_RENDIMIENTO]
        + [(c, nombre_de_indice(claves)) for c, claves, _ in INDICES_DESCARTADOS]
    )
    for coleccion, nombre in todos:
        if nombre in {i["name"] for i in bd[coleccion].list_indexes()}:
            bd[coleccion].drop_index(nombre)


def medir_todas(bd, ids: list[str] | None, corridas: int) -> dict:
    fns = funciones(bd)
    return {i: medicion.medir(bd, fns[i], corridas) for i in (ids or list(fns))}


def medir_descartados(bd, corridas: int) -> list[dict]:
    """Por cada candidato descartado: lo crea, mide las consultas que podría mejorar y lo borra."""
    filas = []
    for coleccion, claves, ids in INDICES_DESCARTADOS:
        nombre = bd[coleccion].create_index(claves)
        try:
            filas.append(
                {
                    "coleccion": coleccion,
                    "nombre": nombre,
                    "con": medir_todas(bd, ids, corridas),
                    "tamano": medicion.tamanos_de_indices(bd, coleccion)[nombre],
                }
            )
        finally:
            bd[coleccion].drop_index(nombre)
    return filas


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


def tabla_descartados(base: dict, filas: list[dict]) -> str:
    """Cada candidato descartado: la consulta que podría mejorar, sin él (con los 4 elegidos) y con él."""
    cabecera = [
        "| Candidato | Consulta | Documentos examinados sin / con | Tiempo (ms) sin / con | Tamaño |",
        "|---|---|---|---|---|",
    ]
    entero = lambda v: f"{v:,}".replace(",", ".")
    for fila in filas:
        for i, con in fila["con"].items():
            sin = base[i]
            cabecera.append(
                f"| {fila['coleccion']} `{fila['nombre']}` | {i} | {entero(sin['docs'])} / {entero(con['docs'])} "
                f"| {sin['ms']:.1f} / {con['ms']:.1f} | {fila['tamano'] / 1024:.1f} KB |"
            )
    return "\n".join(cabecera)


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

    print("\n### Candidatos descartados: qué aportarían (ADR-022)\n")
    print(tabla_descartados(despues, medir_descartados(bd, a.corridas)))

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
