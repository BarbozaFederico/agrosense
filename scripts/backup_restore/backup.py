"""Backup de la base con mongodump, más la rotación de copias viejas (RNF-02, ADR-016).

Qué hace:
    1. Vuelca la base completa en UN archivo comprimido: <base>_AAAAMMDD_HHMMSS.archive.gz.
    2. Escribe junto a él el manifiesto (huella sha256 y resumen de cada colección).
    3. Aplica la política: conserva la última copia de cada uno de los 7 días más recientes y la de los
       4 últimos domingos; borra el resto (con su manifiesto).

Política (supuesto adoptado, ADR-016): un backup por día a las 02:00; 7 diarios y 4 semanales.

Cómo correrlo (desde la raíz, con el entorno virtual activado):
    python -m scripts.backup_restore.backup                       # base "agrosense" (o la de AGROSENSE_BD)
    python -m scripts.backup_restore.backup --bd agrosense_tests --destino C:/algun/lugar --sin-rotar

Los respaldos van fuera del repositorio: ~/agrosense-backups, o la carpeta de AGROSENSE_BACKUP_DIR.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from db.conexion import BASE_POR_DEFECTO, obtener_base, preparar_consola
from scripts.backup_restore.comun import (DIARIOS, SEMANALES, SUFIJO, ErrorDeRespaldo, buscar_herramienta,
                                          directorio_de_respaldos, ejecutar, listar_respaldos, resumen_de_base,
                                          ruta_manifiesto, sha256_de, uri)

DOMINGO = 6


def hacer_backup(nombre_bd: str, carpeta: Path, ahora: datetime | None = None) -> tuple[Path, dict]:
    """Crea el archivo y su manifiesto. Devuelve la ruta y el manifiesto."""
    ahora = ahora or datetime.now()
    bd = obtener_base(nombre_bd)
    if not bd.list_collection_names():
        raise ErrorDeRespaldo(f"La base {nombre_bd} no existe o está vacía: no hay nada que respaldar.")
    archivo = carpeta / f"{nombre_bd}_{ahora:%Y%m%d_%H%M%S}{SUFIJO}"
    try:
        ejecutar([buscar_herramienta("mongodump"), f"--uri={uri()}", f"--db={nombre_bd}",
                  f"--archive={archivo}", "--gzip"])
    except ErrorDeRespaldo:
        archivo.unlink(missing_ok=True)
        raise
    manifiesto = {
        "base": nombre_bd,
        "creado": ahora.isoformat(timespec="seconds"),
        "servidor": bd.client.server_info()["version"],
        "tamano_bytes": archivo.stat().st_size,
        "sha256": sha256_de(archivo),
        "colecciones": resumen_de_base(bd),
    }
    ruta_manifiesto(archivo).write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
    return archivo, manifiesto


def seleccionar_a_borrar(respaldos: list[tuple[Path, datetime]], diarios: int = DIARIOS,
                         semanales: int = SEMANALES) -> list[Path]:
    """Qué copias sobran según la política. No borra nada: solo decide (por eso se puede probar con fechas inventadas)."""
    ultima_del_dia = {}
    for ruta, cuando in sorted(respaldos, key=lambda par: par[1]):
        ultima_del_dia[cuando.date()] = ruta          # la más nueva de cada día pisa a las anteriores
    dias = sorted(ultima_del_dia, reverse=True)
    conservar = set(dias[:diarios]) | set([d for d in dias if d.weekday() == DOMINGO][:semanales])
    conservadas = {ultima_del_dia[d] for d in conservar}
    return [ruta for ruta, _ in respaldos if ruta not in conservadas]


def rotar(carpeta: Path, nombre_bd: str) -> list[Path]:
    """Aplica la política a los backups de la base: borra los archivos que sobran y sus manifiestos."""
    sobran = seleccionar_a_borrar(listar_respaldos(carpeta, nombre_bd))
    for ruta in sobran:
        ruta.unlink()
        ruta_manifiesto(ruta).unlink(missing_ok=True)
    return sobran


def main() -> None:
    preparar_consola()
    parser = argparse.ArgumentParser(description="Backup de la base con mongodump y rotación de copias viejas.")
    parser.add_argument("--bd", default=os.environ.get("AGROSENSE_BD", BASE_POR_DEFECTO), help="base a respaldar")
    parser.add_argument("--destino", help="carpeta de los respaldos (por defecto AGROSENSE_BACKUP_DIR o ~/agrosense-backups)")
    parser.add_argument("--sin-rotar", action="store_true", help="no borrar las copias viejas")
    args = parser.parse_args()
    try:
        carpeta = directorio_de_respaldos(args.destino)
        archivo, manifiesto = hacer_backup(args.bd, carpeta)
        print(f"Backup de {args.bd}: {archivo}")
        print(f"  {manifiesto['tamano_bytes'] / 1024:.0f} KB, sha256 {manifiesto['sha256'][:16]}…, "
              f"MongoDB {manifiesto['servidor']}")
        for nombre, c in manifiesto["colecciones"].items():
            print(f"  {nombre.ljust(27)} {c['documentos']:>8} documentos  {c['tipo']}")
        if not args.sin_rotar:
            borradas = rotar(carpeta, args.bd)
            print(f"Rotación: {len(borradas)} copia(s) borrada(s) ({DIARIOS} diarios + {SEMANALES} semanales)")
            for ruta in borradas:
                print(f"  borrada {ruta.name}")
    except ErrorDeRespaldo as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
