"""Datos de `eventos_climaticos`: la helada de la noche extrema. Esquema: db/schemas/eventos_climaticos.py.

Sale de `configuracion.NOCHE_EXTREMA` (ADR-009, decisión 7): el evento y la configuración
siempre coinciden en finca, ventana y mínima.

Área (Q4): el rectángulo de la finca de San Rafael con 300 m de margen. Alcanza a sus dos
parcelas y deja afuera las de San Martín y Tupungato, que están a decenas de kilómetros.
"""

from bson import ObjectId

from db.seeds.configuracion import NOCHE_EXTREMA
from db.seeds.geometria import rectangulo
from db.seeds.ubicaciones import CENTROS_FINCA, LADO_PARCELA_M, MARGEN_FINCA_M, SEPARACION_M

NOMBRE = "eventos_climaticos"

MARGEN_EVENTO_M = 300

# `_id` fijo: el esquema exige `_id` y la validación previa corre antes de insertar (cuando
# pymongo todavía no se lo agregó). Con un valor fijo, cada corrida del seed da el mismo
# resultado. Es un ObjectId inventado (12 bytes en hexadecimal), solo para el seed.
ID_NOCHE_EXTREMA = ObjectId("5eed00000000000000000001")


def documentos() -> list[dict]:
    ancho = 2 * LADO_PARCELA_M + SEPARACION_M + 2 * MARGEN_FINCA_M + 2 * MARGEN_EVENTO_M
    alto = LADO_PARCELA_M + 2 * MARGEN_FINCA_M + 2 * MARGEN_EVENTO_M
    return [{
        "_id": ID_NOCHE_EXTREMA,
        "tipo": "helada",
        "inicio": NOCHE_EXTREMA["inicio"],
        "fin": NOCHE_EXTREMA["fin"],
        "area": rectangulo(CENTROS_FINCA[NOCHE_EXTREMA["finca_id"]], ancho, alto),
        "temperatura_minima_c": NOCHE_EXTREMA["minimo_c"],   # supuesto, a validar (ADR-009)
        "descripcion": "Noche de helada precargada (RF-13), San Rafael. Datos simulados.",
        "fuente": "seed",
    }]
