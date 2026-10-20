"""Piezas comunes de las consultas Q1 a Q10 (ADR-014).

Una consulta de agregación (`aggregate`) es una tubería: una lista de etapas ($match, $group,
$lookup...) por las que pasan los documentos. En Python es una lista de diccionarios, que el
servidor ejecuta igual que si la mandara `mongosh`.

Cada consulta tiene la misma forma:
    pipeline(...)   devuelve la lista de etapas
    consultar(bd, ...)   la ejecuta y devuelve los documentos (también la usa el dashboard)
    main()          la corre desde la consola: python -m db.queries.qN_nombre --help

Las fechas se reciben en hora de Argentina (UTC-3) o en UTC con zona, y se guardan en UTC.
`pymongo` devuelve las fechas sin zona horaria (siempre UTC): acá se centraliza la conversión.
"""

import argparse
import json
import math
import re
from datetime import date, datetime, timedelta, timezone

from bson import ObjectId

ZONA = "-03:00"                                   # hora de Argentina, para $dateTrunc
DESFASE_LOCAL = timedelta(hours=-3)               # UTC-3
FECHA_NOCHE = date(2026, 10, 5)                   # la noche precargada (RF-13)
FIN_TEMPORADA = date(2027, 3, 31)                 # último día de la temporada simulada

# Mes -> período de `configuracion.umbrales_riego` (ADR-011)
PERIODO_RIEGO = {9: "sep_oct", 10: "sep_oct", 11: "nov", 12: "dic_ene", 1: "dic_ene", 2: "feb_mar", 3: "feb_mar"}
AHORA = datetime(2026, 10, 5, 9, 30, tzinfo=timezone.utc)   # 06:30 hora de Argentina (ADR-012)


# --------------------------------------------------------------------------- fechas

def a_utc(valor: datetime | str) -> datetime:
    """Texto ISO (con Z) o datetime a datetime UTC con zona."""
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def a_hora_local(valor: datetime) -> datetime:
    """Datetime (UTC, con o sin zona) a hora de Argentina, sin zona."""
    return valor.replace(tzinfo=None) + DESFASE_LOCAL if valor.tzinfo is None else \
        (valor.astimezone(timezone.utc) + DESFASE_LOCAL).replace(tzinfo=None)


def a_fecha(valor: date | str) -> date:
    return date.fromisoformat(valor) if isinstance(valor, str) else valor


def medianoche_local(fecha: date) -> datetime:
    """Las 00:00 de hora de Argentina de ese día, como UTC con zona (03:00Z)."""
    return datetime(fecha.year, fecha.month, fecha.day, tzinfo=timezone.utc) - DESFASE_LOCAL


def ventana_noche(fecha: date) -> tuple[datetime, datetime]:
    """(inicio, fin) UTC de la noche de la mañana `fecha`: de las 18:00 del día anterior a las 12:00
    del día `fecha`, hora de Argentina (ADR-014)."""
    inicio = medianoche_local(fecha) - timedelta(hours=6)
    fin = medianoche_local(fecha) + timedelta(hours=12)
    return inicio, fin


# --------------------------------------------------------------------------- configuración

def configuracion(bd) -> dict:
    """El documento de `configuracion` (Δ, nodo inactivo, cortes del riesgo, umbrales de riego)."""
    doc = bd.configuracion.find_one({"_id": "general"})
    if doc is None:
        raise SystemExit("Falta la configuración en la base: corré primero  python -m db.seeds.cargar")
    return doc


# --------------------------------------------------------------------------- consola

def parser(descripcion: str) -> argparse.ArgumentParser:
    """Parser de argumentos de la consola, con la opción de mostrar el texto de mongosh."""
    p = argparse.ArgumentParser(description=descripcion, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--mongosh", action="store_true",
                   help="muestra la misma consulta escrita para mongosh (sin ejecutarla)")
    return p


def _formato(valor) -> str:
    if isinstance(valor, datetime):
        local = a_hora_local(valor)
        return f"{local:%d/%m/%Y}" if (local.hour, local.minute) == (0, 0) else f"{local:%d/%m/%Y %H:%M}"
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else f"{valor:.2f}"
    if isinstance(valor, list):
        return ", ".join(str(v) for v in valor) if valor else "-"
    return "-" if valor is None else str(valor)


def imprimir_tabla(filas: list[dict], columnas: list[str]) -> None:
    """Muestra los documentos como una tabla de texto (las fechas en hora de Argentina)."""
    if not filas:
        print("(sin resultados)")
        return
    celdas = [[_formato(f.get(c)) for c in columnas] for f in filas]
    anchos = [max(len(c), *(len(fila[i]) for fila in celdas)) for i, c in enumerate(columnas)]
    print("  ".join(c.ljust(a) for c, a in zip(columnas, anchos)))
    print("  ".join("-" * a for a in anchos))
    for fila in celdas:
        print("  ".join(c.ljust(a) for c, a in zip(fila, anchos)))


# --------------------------------------------------------------------------- texto de mongosh

_IDENTIFICADOR = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def a_js(valor, nivel: int = 0) -> str:
    """Escribe un valor de Python (diccionarios, listas, fechas...) como código de mongosh."""
    sangria = "  " * (nivel + 1)
    cierre = "  " * nivel
    if isinstance(valor, dict):
        if not valor:
            return "{}"
        partes = [f"{sangria}{k if _IDENTIFICADOR.match(k) else json.dumps(k)}: {a_js(v, nivel + 1)}"
                  for k, v in valor.items()]
        return "{\n" + ",\n".join(partes) + f"\n{cierre}}}"
    if isinstance(valor, (list, tuple)):
        if not valor:
            return "[]"
        if all(not isinstance(v, (dict, list, tuple)) for v in valor):
            return "[" + ", ".join(a_js(v, nivel) for v in valor) + "]"
        partes = [f"{sangria}{a_js(v, nivel + 1)}" for v in valor]
        return "[\n" + ",\n".join(partes) + f"\n{cierre}]"
    if isinstance(valor, datetime):
        return f'ISODate("{a_utc(valor):%Y-%m-%dT%H:%M:%S}.000Z")'
    if isinstance(valor, ObjectId):
        return f'ObjectId("{valor}")'
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if valor is None:
        return "null"
    if isinstance(valor, float):
        return "Infinity" if math.isinf(valor) else repr(valor)
    if isinstance(valor, (int, str)):
        return json.dumps(valor, ensure_ascii=False)
    raise TypeError(f"No sé escribir {type(valor).__name__} para mongosh")


def texto_mongosh(coleccion: str, pipeline: list) -> str:
    """La consulta escrita para mongosh: se puede pegar tal cual en la consola o en Compass."""
    return f"db.{coleccion}.aggregate({a_js(pipeline)})"
