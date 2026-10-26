"""Piezas comunes del backup y la restauración (ADR-016).

Qué hay acá:
    - dónde están mongodump y mongorestore, y dónde se guardan los respaldos (siempre fuera del repositorio);
    - el manifiesto: un archivo chico junto a cada backup con la huella (sha256), el tamaño y el resumen de la
      base en ese momento (documentos, índices y validador de cada colección). Sirve para comprobar que el
      archivo no cambió y que la restauración dejó la base igual, aunque la original ya no exista;
    - la comparación de dos bases y de los resultados de las consultas.

El manifiesto solo guarda conteos y nombres: no tiene datos de las lecturas ni credenciales.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from bson import json_util

from db.conexion import URI_POR_DEFECTO

RAIZ = Path(__file__).resolve().parents[2]  # scripts/backup_restore/comun.py → raíz del repositorio
DIARIOS = 7  # política (supuesto adoptado, ADR-016): copias de los últimos 7 días...
SEMANALES = 4  # ...y de los últimos 4 domingos
SUFIJO = ".archive.gz"
PATRON = re.compile(r"^(?P<bd>.+)_(?P<dia>\d{8})_(?P<hora>\d{6})\.archive\.gz$")
CONSULTAS_A_COMPARAR = ("Q1", "Q5", "Q9", "Q10")


class ErrorDeRespaldo(Exception):
    """Algo impide hacer o restaurar el backup. El mensaje dice qué pasó y qué hacer."""


def uri() -> str:
    return os.environ.get("AGROSENSE_URI", URI_POR_DEFECTO)


def buscar_herramienta(nombre: str) -> str:
    """Ruta de mongodump o mongorestore: AGROSENSE_HERRAMIENTAS, el PATH, o la carpeta que usa el instalador de Windows."""
    carpeta = os.environ.get("AGROSENSE_HERRAMIENTAS")
    if carpeta and (ruta := shutil.which(nombre, path=carpeta)):
        return ruta
    if ruta := shutil.which(nombre):
        return ruta
    instalaciones = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "MongoDB" / "Tools"
    for bin_ in sorted(instalaciones.glob("*/bin"), reverse=True):
        if ruta := shutil.which(nombre, path=str(bin_)):
            return ruta
    raise ErrorDeRespaldo(
        f"No encuentro {nombre}. Instalá MongoDB Database Tools (winget install MongoDB.DatabaseTools) "
        "o indicá su carpeta en la variable AGROSENSE_HERRAMIENTAS."
    )


def directorio_de_respaldos(destino: str | Path | None = None) -> Path:
    """La carpeta de los respaldos (AGROSENSE_BACKUP_DIR o ~/agrosense-backups). Nunca dentro del repositorio (RNF-07)."""
    carpeta = Path(destino or os.environ.get("AGROSENSE_BACKUP_DIR") or Path.home() / "agrosense-backups")
    carpeta = carpeta.expanduser().resolve()
    if carpeta == RAIZ or RAIZ in carpeta.parents:
        raise ErrorDeRespaldo(
            f"{carpeta} está dentro del repositorio, que es público. Elegí una carpeta afuera "
            "(opción --destino o variable AGROSENSE_BACKUP_DIR)."
        )
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def ejecutar(comando: list[str]) -> None:
    """Corre una herramienta de MongoDB; si falla, muestra sus últimas líneas."""
    p = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        ultimas = "\n".join(p.stderr.strip().splitlines()[-5:])
        raise ErrorDeRespaldo(f"{Path(comando[0]).stem} terminó con error {p.returncode}:\n{ultimas}")


# --- Archivos de respaldo


def listar_respaldos(carpeta: Path, bd: str) -> list[tuple[Path, datetime]]:
    """Los backups de `bd` en la carpeta, del más viejo al más nuevo, con la fecha que dice su nombre."""
    encontrados = []
    for ruta in carpeta.glob(f"*{SUFIJO}"):
        m = PATRON.match(ruta.name)
        if m and m["bd"] == bd:
            encontrados.append((ruta, datetime.strptime(m["dia"] + m["hora"], "%Y%m%d%H%M%S")))
    return sorted(encontrados, key=lambda par: par[1])


def base_de_origen(archivo: Path) -> str:
    """La base de la que salió el backup, según el nombre del archivo."""
    m = PATRON.match(archivo.name)
    if not m:
        raise ErrorDeRespaldo(f"{archivo.name} no tiene el nombre de un backup (base_AAAAMMDD_HHMMSS{SUFIJO}).")
    return m["bd"]


def ruta_manifiesto(archivo: Path) -> Path:
    return archivo.with_name(archivo.name[: -len(SUFIJO)] + ".manifiesto.json")


def sha256_de(archivo: Path) -> str:
    h = hashlib.sha256()
    with archivo.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def integro(archivo: Path, manifiesto: dict) -> bool:
    """¿El archivo es el mismo que se guardó? (misma huella que dice el manifiesto)"""
    return sha256_de(archivo) == manifiesto["sha256"]


def leer_manifiesto(archivo: Path) -> dict | None:
    ruta = ruta_manifiesto(archivo)
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


# --- Resumen y comparación de bases


def resumen_de_base(bd) -> dict:
    """Por colección: tipo, documentos, nombres de índices y huella del validador."""
    resumen = {}
    for info in bd.list_collections():
        nombre = info["name"]
        if nombre.startswith("system."):
            continue
        validador = info["options"].get("validator")
        huella = (
            hashlib.sha256(json.dumps(validador, sort_keys=True, default=str).encode()).hexdigest()[:12]
            if validador
            else None
        )
        resumen[nombre] = {
            "tipo": info["type"],
            "documentos": bd[nombre].count_documents({}),
            "indices": sorted(bd[nombre].index_information()),
            "validador": huella,
        }
    return resumen


def comparar_resumenes(esperado: dict, obtenido: dict) -> list[str]:
    """Las diferencias entre dos resúmenes (lista vacía = iguales)."""
    diferencias = []
    for nombre in sorted(set(esperado) | set(obtenido)):
        if nombre not in obtenido:
            diferencias.append(f"{nombre}: falta en la base restaurada")
        elif nombre not in esperado:
            diferencias.append(f"{nombre}: sobra en la base restaurada")
        else:
            for campo in ("tipo", "documentos", "indices", "validador"):
                if esperado[nombre][campo] != obtenido[nombre][campo]:
                    diferencias.append(
                        f"{nombre}: {campo} esperado {esperado[nombre][campo]!r}, "
                        f"obtenido {obtenido[nombre][campo]!r}"
                    )
    return diferencias


def normalizar(resultado) -> str:
    """El resultado de una consulta como texto comparable (sin depender del orden de los campos)."""
    return json.dumps(json.loads(json_util.dumps(resultado)), sort_keys=True)


def comparar_consultas(bd_a, bd_b, ids=CONSULTAS_A_COMPARAR) -> list[tuple[str, bool]]:
    """Corre las consultas en las dos bases y dice si devuelven exactamente lo mismo."""
    from db.indexes.medir_indices import funciones

    fa, fb = funciones(bd_a), funciones(bd_b)
    return [(i, normalizar(fa[i]()) == normalizar(fb[i]())) for i in ids]
