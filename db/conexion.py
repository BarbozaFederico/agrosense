"""Conexión a MongoDB.

Lee dos variables de entorno, para no escribir datos de conexión en el código
(el repositorio es público):
    AGROSENSE_URI  dirección del servidor (por defecto, el MongoDB local)
    AGROSENSE_BD   nombre de la base (por defecto, "agrosense")

Ejemplo en Git Bash, para trabajar sobre la base de prueba:
    AGROSENSE_BD=agrosense_tests python -m db.schemas.crear_colecciones
"""

import os
import sys

from pymongo import MongoClient
from pymongo.database import Database

URI_POR_DEFECTO = "mongodb://localhost:27017"
BASE_POR_DEFECTO = "agrosense"


def obtener_base(nombre: str | None = None) -> Database:
    """Devuelve la base indicada (o la de AGROSENSE_BD, o "agrosense")."""
    uri = os.environ.get("AGROSENSE_URI", URI_POR_DEFECTO)
    nombre = nombre or os.environ.get("AGROSENSE_BD", BASE_POR_DEFECTO)
    return MongoClient(uri)[nombre]


def preparar_consola() -> None:
    """La consola de Windows no usa UTF-8: lo forzamos para ver bien los acentos."""
    sys.stdout.reconfigure(encoding="utf-8")
