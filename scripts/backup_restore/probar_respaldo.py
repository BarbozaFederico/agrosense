"""Prueba del backup y la restauración.

Pregunta: ¿el backup se hace, se rota según la política, se restaura igual y se niega a hacer cosas peligrosas?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m scripts.backup_restore.probar_respaldo

Usa la base de PRUEBA `agrosense_tests` (si está vacía, carga el seed y la temporada ahí) y una carpeta temporal
fuera del repositorio. Restaura en `agrosense_tests_restaurada` y la borra al terminar. No toca `agrosense`.
Tarda unos segundos.
"""

import contextlib
import io
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from db.conexion import obtener_base, preparar_consola
from db.indexes.crear_indices import crear_indices, crear_indices_rendimiento
from db.schemas.probar_esquemas import Resumen
from scripts.backup_restore import backup, restaurar
from scripts.backup_restore.comun import (
    RAIZ,
    ErrorDeRespaldo,
    buscar_herramienta,
    comparar_consultas,
    comparar_resumenes,
    directorio_de_respaldos,
    integro,
    leer_manifiesto,
    resumen_de_base,
    ruta_manifiesto,
)

ORIGEN = "agrosense_tests"
COPIA = "agrosense_tests_restaurada"
CORRUPTA = "agrosense_tests_corrupta"


def fabricar(carpeta: Path, fechas: list[datetime], modelo: Path) -> list[tuple[Path, datetime]]:
    """Copia el backup real (y su manifiesto) con otros nombres, como si se hubieran hecho en esas fechas."""
    creados = []
    for cuando in fechas:
        destino = carpeta / f"{ORIGEN}_{cuando:%Y%m%d_%H%M%S}.archive.gz"
        shutil.copy(modelo, destino)
        shutil.copy(ruta_manifiesto(modelo), ruta_manifiesto(destino))
        creados.append((destino, cuando))
    return creados


def lanza(funcion, *args, **kwargs) -> bool:
    try:
        funcion(*args, **kwargs)
    except ErrorDeRespaldo:
        return True
    return False


def main() -> None:
    preparar_consola()
    r = Resumen()
    bd = obtener_base(ORIGEN)
    if bd.lecturas.estimated_document_count() == 0:
        from db.seeds import cargar as cargar_seed
        from simulator import generar

        with contextlib.redirect_stdout(io.StringIO()):
            cargar_seed.cargar(bd)
            generar.escribir(bd, generar.simular(generar.cargar_contexto(bd)))
    indices = crear_indices(bd) + crear_indices_rendimiento(bd)  # las pruebas de índices los dejan borrados
    cliente = bd.client
    cliente.drop_database(COPIA)
    cliente.drop_database(CORRUPTA)
    print(f"Base de prueba: {ORIGEN} (se restaura en {COPIA}; la base real no se toca)")

    print("--- Política de rotación (con fechas inventadas, sin tocar archivos)")
    inicio = datetime(2026, 9, 1, 2, 0)
    diarias = [(Path(f"copia_{i}.gz"), inicio + timedelta(days=i)) for i in range(51)]  # 1/9 a 21/10, a las 02:00
    extra = (Path("extra_21_oct.gz"), datetime(2026, 10, 21, 20, 0))  # una segunda copia el mismo día
    borrar = backup.seleccionar_a_borrar(diarias + [extra])
    conservadas = {ruta.name for ruta, _ in diarias + [extra]} - {ruta.name for ruta in borrar}
    # A mano: 21/10/2026 es miércoles. 7 diarios = del 15 al 21/10. Domingos: 18/10 (ya incluido), 11/10, 4/10 y 27/9.
    esperadas = (
        {f"copia_{(date(2026, 10, d) - date(2026, 9, 1)).days}.gz" for d in (15, 16, 17, 18, 19, 20)}
        | {"extra_21_oct.gz"}
        | {
            f"copia_{(date(2026, 10, 11) - date(2026, 9, 1)).days}.gz",
            f"copia_{(date(2026, 10, 4) - date(2026, 9, 1)).days}.gz",
            f"copia_{(date(2026, 9, 27) - date(2026, 9, 1)).days}.gz",
        }
    )
    r.chequear(
        conservadas == esperadas,
        f"rotación | de 52 copias se conservan 10: los 7 días del 15 al 21/10 y los domingos 11/10, 4/10 y 27/9 "
        f"(quedan {len(conservadas)})",
    )
    r.chequear(
        "copia_50.gz" in {ruta.name for ruta in borrar} and "extra_21_oct.gz" not in {ruta.name for ruta in borrar},
        "rotación | de dos copias del mismo día queda la más nueva (la de las 20:00)",
    )
    r.chequear(
        backup.seleccionar_a_borrar(diarias[:5]) == [] and backup.seleccionar_a_borrar([]) == [],
        "rotación | con pocas copias, o ninguna, no se borra nada",
    )

    print("--- Dónde se guarda")
    r.chequear(
        lanza(directorio_de_respaldos, RAIZ / "backups") and lanza(directorio_de_respaldos, RAIZ),
        "ubicación | se niega a guardar dentro del repositorio (público, RNF-07)",
    )
    r.chequear(
        Path(buscar_herramienta("mongodump")).exists() and Path(buscar_herramienta("mongorestore")).exists(),
        "herramientas | encuentra mongodump y mongorestore",
    )

    with tempfile.TemporaryDirectory(prefix="agrosense-prueba-") as tmp:
        carpeta = directorio_de_respaldos(Path(tmp) / "respaldos")
        print("--- Backup real de la base de prueba")
        archivo, manifiesto = backup.hacer_backup(ORIGEN, carpeta, datetime(2026, 10, 21, 2, 0))
        resumen_vivo = resumen_de_base(bd)
        r.chequear(
            archivo.name == f"{ORIGEN}_20261021_020000.archive.gz"
            and archivo.stat().st_size > 0
            and ruta_manifiesto(archivo).exists(),
            f"backup | se crea {archivo.name} ({archivo.stat().st_size / 1024:.0f} KB) y su manifiesto",
        )
        r.chequear(
            manifiesto["colecciones"] == resumen_vivo and len(resumen_vivo) == 10,
            "backup | el manifiesto describe las 10 colecciones, con los mismos conteos que la base",
        )
        r.chequear(
            resumen_vivo["lecturas"]["tipo"] == "timeseries" and resumen_vivo["lecturas"]["documentos"] > 700_000,
            f"backup | lecturas es una serie temporal con {resumen_vivo['lecturas']['documentos']:,} lecturas",
        )
        r.chequear(
            integro(archivo, leer_manifiesto(archivo)),
            "integridad | la huella sha256 del archivo coincide con la del manifiesto",
        )

        print("--- Restauración a una base aparte")
        diferencias = restaurar.restaurar(archivo, COPIA)
        r.chequear(
            diferencias == [],
            f"restaurar | {COPIA} coincide con el manifiesto (tipo, documentos, índices y validadores)"
            + (f": {diferencias}" if diferencias else ""),
        )
        restauradas = resumen_de_base(cliente[COPIA])
        r.chequear(
            restauradas["lecturas"]["tipo"] == "timeseries"
            and restauradas["lecturas"]["documentos"] == resumen_vivo["lecturas"]["documentos"],
            "restaurar | lecturas volvió a ser una serie temporal con todas sus lecturas",
        )
        indices_restaurados = {nombre for c in restauradas.values() for nombre in c["indices"]}
        r.chequear(
            len(indices) == 7 and set(indices) <= indices_restaurados and "meta_1_ts_1" in indices_restaurados,
            f"restaurar | volvieron los {len(indices)} índices del proyecto (3 2dsphere y 4 de rendimiento) "
            "y el automático de la serie temporal",
        )
        comparacion = comparar_consultas(bd, cliente[COPIA])
        r.chequear(
            all(igual for _, igual in comparacion),
            "restaurar | " + ", ".join(i for i, _ in comparacion) + " devuelven exactamente lo mismo en las dos bases",
        )

        print("--- Protecciones")
        antes = bd.alertas.count_documents({})
        r.chequear(lanza(restaurar.restaurar, archivo, COPIA), f"proteger | no pisa {COPIA} si ya existe")
        r.chequear(
            lanza(restaurar.restaurar, archivo, ORIGEN) and bd.alertas.count_documents({}) == antes,
            f"proteger | no pisa la base original {ORIGEN} sin --reemplazar y sus datos siguen intactos",
        )
        torcida = carpeta / f"{ORIGEN}_20261022_020000.archive.gz"
        shutil.copy(archivo, torcida)
        shutil.copy(ruta_manifiesto(archivo), ruta_manifiesto(torcida))
        contenido = bytearray(torcida.read_bytes())
        contenido[len(contenido) // 2] ^= 0xFF
        torcida.write_bytes(contenido)
        r.chequear(
            not integro(torcida, leer_manifiesto(torcida))
            and lanza(restaurar.restaurar, torcida, CORRUPTA)
            and CORRUPTA not in cliente.list_database_names(),
            "integridad | un archivo con un byte cambiado se detecta y no se restaura nada",
        )
        torcida.unlink()
        ruta_manifiesto(torcida).unlink()

        print("--- Simulacro de desastre (sobre la copia)")
        cliente[COPIA].riegos.drop()
        cliente[COPIA].alertas.delete_many({})
        dano = comparar_resumenes(manifiesto["colecciones"], resumen_de_base(cliente[COPIA]))
        r.chequear(
            len(dano) == 2
            and any(d.startswith("riegos:") for d in dano)
            and any(d.startswith("alertas:") for d in dano),
            "desastre | se borra riegos y se vacía alertas en la copia, y la comparación lo detecta: "
            + "; ".join(dano),
        )
        diferencias = restaurar.restaurar(archivo, COPIA, reemplazar=True)
        r.chequear(
            diferencias == []
            and cliente[COPIA].riegos.count_documents({}) == resumen_vivo["riegos"]["documentos"]
            and cliente[COPIA].alertas.count_documents({}) == resumen_vivo["alertas"]["documentos"],
            f"desastre | con --reemplazar vuelven {resumen_vivo['riegos']['documentos']} riegos y "
            f"{resumen_vivo['alertas']['documentos']} alertas, y la copia queda igual al manifiesto",
        )

        print("--- Rotación sobre archivos reales")
        otra = directorio_de_respaldos(Path(tmp) / "rotacion")
        fechas = [datetime(2026, 10, 12, 2, 0) + timedelta(days=i) for i in range(10)]  # lunes 12 a miércoles 21/10
        fabricar(otra, fechas, archivo)
        borradas = backup.rotar(otra, ORIGEN)
        quedan = sorted(p.name for p in otra.glob("*.archive.gz"))
        r.chequear(
            sorted(p.name for p in borradas) == [f"{ORIGEN}_202610{d}_020000.archive.gz" for d in (12, 13, 14)]
            and len(quedan) == 7
            and len(list(otra.glob("*.manifiesto.json"))) == 7,
            "rotar | de 10 copias reales se borran las 3 más viejas (12, 13 y 14/10) y quedan 7, cada una con su manifiesto",
        )
    cliente.drop_database(COPIA)

    print("---")
    print(
        f"RESULTADO: todos los casos dieron lo esperado ({r.total} casos)"
        if r.fallas == 0
        else f"RESULTADO: {r.fallas} de {r.total} casos NO dieron lo esperado"
    )
    if r.fallas:
        sys.exit(1)


if __name__ == "__main__":
    main()
