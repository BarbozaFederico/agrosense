"""Crea las 10 colecciones de agrosense con sus validaciones.

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.schemas.crear_colecciones

Por defecto usa la base `agrosense`. Para otra base, definir AGROSENSE_BD
(en Git Bash):
    AGROSENSE_BD=agrosense_tests python -m db.schemas.crear_colecciones

Se puede correr más de una vez: si una colección ya existe, actualiza su
validador con collMod y NO borra datos.

"python -m" ejecuta el archivo como parte del paquete `db`, así los
"from db.schemas import ..." funcionan desde la raíz del repo.
"""

from db.conexion import obtener_base, preparar_consola
from db.schemas.crear import crear_colecciones


def main() -> None:
    preparar_consola()
    bd = obtener_base()
    version = bd.client.server_info()["version"]
    print(f"Versión del servidor: {version} | base: {bd.name}")
    print("---")
    crear_colecciones(bd)
    print("---")
    nombres = sorted(n for n in bd.list_collection_names() if not n.startswith("system."))
    print(f"Colecciones en {bd.name}: {', '.join(nombres)}")


if __name__ == "__main__":
    main()
