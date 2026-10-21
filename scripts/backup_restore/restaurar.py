"""Restauración de un backup con mongorestore y verificación del resultado (RNF-03, ADR-016).

Qué hace:
    1. Comprueba que el archivo no cambió (huella sha256 del manifiesto).
    2. Restaura en una base APARTE (por defecto <base>_restaurada); nunca pisa una base que ya existe,
       salvo que se pida con --reemplazar.
    3. Compara la base restaurada con el manifiesto: tipo, documentos, índices y validador de cada colección.
    4. Con --comparar-con, corre Q1, Q5, Q9 y Q10 en las dos bases y comprueba que den lo mismo.

Cómo correrlo (desde la raíz, con el entorno virtual activado):
    python -m scripts.backup_restore.restaurar                    # el último backup de "agrosense"
    python -m scripts.backup_restore.restaurar RUTA_DEL_ARCHIVO --destino prueba --comparar-con agrosense
    python -m scripts.backup_restore.restaurar --reemplazar       # desastre: vuelve a dejar "agrosense" como estaba
"""

import argparse
import os
import sys
from pathlib import Path

from db.conexion import BASE_POR_DEFECTO, obtener_base, preparar_consola
from scripts.backup_restore.comun import (CONSULTAS_A_COMPARAR, ErrorDeRespaldo, base_de_origen, buscar_herramienta,
                                          comparar_consultas, comparar_resumenes, directorio_de_respaldos, ejecutar,
                                          integro, leer_manifiesto, listar_respaldos, resumen_de_base, uri)


def restaurar(archivo: Path, destino: str | None = None, reemplazar: bool = False) -> list[str]:
    """Restaura el backup. Devuelve las diferencias contra el manifiesto (lista vacía = quedó igual)."""
    origen = base_de_origen(archivo)
    destino = destino or f"{origen}_restaurada"
    manifiesto = leer_manifiesto(archivo)
    if manifiesto and not integro(archivo, manifiesto):
        raise ErrorDeRespaldo(f"{archivo.name} está dañado o cambió desde que se hizo: la huella no coincide. No se restaura.")
    bd = obtener_base(destino)
    if bd.list_collection_names() and not reemplazar:
        raise ErrorDeRespaldo(f"La base {destino} ya existe. Usá otro --destino, o --reemplazar para sobrescribirla.")

    comando = [buscar_herramienta("mongorestore"), f"--uri={uri()}", f"--archive={archivo}", "--gzip",
               f"--nsInclude={origen}.*"]
    if destino != origen:
        comando += [f"--nsFrom={origen}.*", f"--nsTo={destino}.*"]
    if reemplazar:
        comando.append("--drop")                   # borra cada colección antes de restaurarla
    ejecutar(comando)

    if manifiesto is None:
        return ["no hay manifiesto junto al archivo: la restauración no se pudo verificar"]
    return comparar_resumenes(manifiesto["colecciones"], resumen_de_base(bd))


def main() -> None:
    preparar_consola()
    parser = argparse.ArgumentParser(description="Restaura un backup en una base aparte y verifica el resultado.")
    parser.add_argument("archivo", nargs="?", help="archivo .archive.gz (por defecto, el último de --bd)")
    parser.add_argument("--bd", default=os.environ.get("AGROSENSE_BD", BASE_POR_DEFECTO),
                        help="base cuyo último backup se restaura, si no se da el archivo")
    parser.add_argument("--destino", help="base donde restaurar (por defecto <base>_restaurada)")
    parser.add_argument("--reemplazar", action="store_true", help="sobrescribir la base destino si existe")
    parser.add_argument("--comparar-con", metavar="BASE", help="base contra la que comparar Q1, Q5, Q9 y Q10")
    parser.add_argument("--carpeta", help="carpeta de los respaldos (por defecto AGROSENSE_BACKUP_DIR o ~/agrosense-backups)")
    args = parser.parse_args()
    try:
        if args.archivo:
            archivo = Path(args.archivo)
        else:
            respaldos = listar_respaldos(directorio_de_respaldos(args.carpeta), args.bd)
            if not respaldos:
                raise ErrorDeRespaldo(f"No hay backups de {args.bd}. Hacé uno con: python -m scripts.backup_restore.backup")
            archivo = respaldos[-1][0]
        if not archivo.exists():
            raise ErrorDeRespaldo(f"No existe {archivo}")
        destino = args.destino or f"{base_de_origen(archivo)}_restaurada"
        print(f"Restaurando {archivo.name} en la base {destino}…")
        diferencias = restaurar(archivo, destino, args.reemplazar)
        resumen = resumen_de_base(obtener_base(destino))
        for nombre, c in resumen.items():
            print(f"  {nombre.ljust(27)} {c['documentos']:>8} documentos  {c['tipo']}  {len(c['indices'])} índices")
        fallas = list(diferencias)
        if args.comparar_con:
            for consulta, igual in comparar_consultas(obtener_base(args.comparar_con), obtener_base(destino)):
                print(f"  {consulta}: {'igual en las dos bases' if igual else 'DISTINTA'}")
                if not igual:
                    fallas.append(f"{consulta} devuelve otro resultado")
        if fallas:
            print("RESULTADO: la restauración NO quedó igual:")
            for f in fallas:
                print(f"  - {f}")
            sys.exit(1)
        print("RESULTADO: la base restaurada coincide con el manifiesto"
              + (f" y con {args.comparar_con} en {', '.join(CONSULTAS_A_COMPARAR)}" if args.comparar_con else ""))
    except ErrorDeRespaldo as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
