"""Ayudas para armar las geometrías ficticias del seed (ADR-010, decisión 2).

Una geometría GeoJSON usa grados: [longitud, latitud]. Para dibujar un cuadrado de
141 m de lado hay que pasar metros a grados:
    1 grado de latitud  ≈ 111.320 m en todas partes.
    1 grado de longitud ≈ 111.320 m × cos(latitud): se achica hacia los polos.
Es una aproximación plana, suficiente para rectángulos de cientos de metros.

El anillo de un polígono va en sentido antihorario y se cierra repitiendo el primer
punto (así lo espera el índice 2dsphere).
"""

import math

METROS_POR_GRADO = 111_320


def _a_grados(centro: tuple[float, float], este_m: float, norte_m: float) -> list[float]:
    """Punto a `este_m` metros al este y `norte_m` al norte de `centro` (longitud, latitud)."""
    longitud, latitud = centro
    d_lat = norte_m / METROS_POR_GRADO
    d_lon = este_m / (METROS_POR_GRADO * math.cos(math.radians(latitud)))
    return [round(longitud + d_lon, 6), round(latitud + d_lat, 6)]


def punto(centro: tuple[float, float], este_m: float = 0, norte_m: float = 0) -> dict:
    """Punto GeoJSON desplazado del centro (en metros)."""
    return {"type": "Point", "coordinates": _a_grados(centro, este_m, norte_m)}


def rectangulo(centro: tuple[float, float], ancho_m: float, alto_m: float) -> dict:
    """Polígono GeoJSON rectangular de `ancho_m` × `alto_m` centrado en `centro`."""
    mitad_x, mitad_y = ancho_m / 2, alto_m / 2
    anillo = [
        _a_grados(centro, -mitad_x, -mitad_y),   # suroeste
        _a_grados(centro, +mitad_x, -mitad_y),   # sureste
        _a_grados(centro, +mitad_x, +mitad_y),   # noreste
        _a_grados(centro, -mitad_x, +mitad_y),   # noroeste
    ]
    anillo.append(anillo[0])                     # se cierra con el primer punto
    return {"type": "Polygon", "coordinates": [anillo]}
