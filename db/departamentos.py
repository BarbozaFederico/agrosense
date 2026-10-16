"""Traduce el nombre de un departamento a la clave que se usa en `configuracion`.

En `fincas.departamento` el valor es texto con tilde ("San Martín"); en los campos de
`configuracion` las claves van en snake_case y sin tildes (CLAUDE.md, sección 2):
"San Rafael" → "san_rafael", "San Martín" → "san_martin".
"""

import unicodedata


def clave_departamento(nombre: str) -> str:
    """Quita tildes, pasa a minúsculas y reemplaza los espacios por guiones bajos."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre)
                         if unicodedata.category(c) != "Mn")
    return sin_tildes.lower().replace(" ", "_")
