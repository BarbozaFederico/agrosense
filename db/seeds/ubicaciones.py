"""Ubicación ficticia de las 3 fincas, sus 6 parcelas y sus 12 nodos (ADR-010).

Un solo lugar para las medidas, de donde salen `fincas`, `parcelas` y `nodos`:
así la finca contiene a sus parcelas y cada nodo cae dentro de su parcela por
construcción.

TODO ES FICTICIO: los centros son coordenadas aproximadas dentro de cada departamento,
no representan fincas reales. A validar: que el punto quede dentro del departamento.

Esquema de cada finca (vista desde arriba, el este a la derecha):

    +------------------- finca (parcelas + margen) -------------------+
    |   +------------ parcela 1 ----+   +------------ parcela 2 ----+ |
    |   |  nodo B             .     |   |  nodo B             .     | |
    |   |       .       nodo A      |   |       .       nodo A      | |
    |   +---------------------------+   +---------------------------+ |
    +----------------------------------------------------------------+
"""

import math

from db.seeds.geometria import punto, rectangulo

# Superficie de cada parcela: 2 ha (supuesto, docs/investigacion/vid-malbec.md).
SUPERFICIE_HA = 2
LADO_PARCELA_M = math.sqrt(SUPERFICIE_HA * 10_000)   # ~141,42 m: un cuadrado de 2 ha
SEPARACION_M = 20                                     # camino entre las dos parcelas
MARGEN_FINCA_M = 30                                   # borde de la finca alrededor de sus parcelas

# Los nodos se ubican a un cuarto del lado, desde el centro de su parcela: A al noreste
# y B al suroeste. Dentro de la parcela, lejos del borde.
DESPLAZAMIENTO_NODO_M = LADO_PARCELA_M / 4

# Centro (longitud, latitud) de cada finca, ficticio. Datos de la finca: ver fincas.py.
CENTROS_FINCA = {
    "F-SR": (-68.33, -34.61),    # San Rafael
    "F-SM": (-68.47, -33.08),    # San Martín
    "F-TU": (-69.17, -33.36),    # Tupungato
}

# Códigos de las parcelas de cada finca.
PARCELAS_DE_FINCA = {
    "F-SR": ["P-SR-1", "P-SR-2"],
    "F-SM": ["P-SM-1", "P-SM-2"],
    "F-TU": ["P-TU-1", "P-TU-2"],
}


def centro_parcela(parcela_id: str) -> tuple[float, float]:
    """Centro de la parcela: la primera al oeste y la segunda al este del centro de la finca."""
    finca_id = "F-" + parcela_id.split("-")[1]
    numero = int(parcela_id.split("-")[2])
    corrimiento_m = (LADO_PARCELA_M + SEPARACION_M) / 2 * (-1 if numero == 1 else 1)
    return punto(CENTROS_FINCA[finca_id], este_m=corrimiento_m)["coordinates"]


def geometria_parcela(parcela_id: str) -> dict:
    return rectangulo(centro_parcela(parcela_id), LADO_PARCELA_M, LADO_PARCELA_M)


def geometria_finca(finca_id: str) -> dict:
    """Rectángulo que envuelve las 2 parcelas, con un margen."""
    ancho = 2 * LADO_PARCELA_M + SEPARACION_M + 2 * MARGEN_FINCA_M
    alto = LADO_PARCELA_M + 2 * MARGEN_FINCA_M
    return rectangulo(CENTROS_FINCA[finca_id], ancho, alto)


def ubicacion_nodo(nodo_id: str) -> dict:
    """Punto del nodo `N-SR-1-A` dentro de su parcela `P-SR-1`."""
    _, depto, numero, letra = nodo_id.split("-")
    signo = 1 if letra == "A" else -1
    return punto(centro_parcela(f"P-{depto}-{numero}"),
                 este_m=signo * DESPLAZAMIENTO_NODO_M, norte_m=signo * DESPLAZAMIENTO_NODO_M)
