"""Datos de `configuracion`: un solo documento, `_id: "general"`. Esquema: db/schemas/configuracion.py.

Cada valor lleva al lado su marca y su fuente (ADR-005 y ADR-009).
"""

from datetime import datetime, timezone

from db.seeds import umbrales_riego

NOMBRE = "configuracion"

# Noche extrema precargada (RF-13, ADR-009). San Rafael, primera semana de octubre de 2026.
#   inicio y fin: 5/10/2026 de 03:00 a 08:00 hora de Argentina (UTC-3), o sea 06:00 a 11:00 UTC.
#     Fijadas en ADR-012 (decisión 3): el simulador calibra el clima de setiembre de San Rafael
#     para que las parcelas estén en BBCH 07 o más esa noche, y se comprueba con Q9.
#   minimo_c: -6,3 °C en el sensor. Supuesto adoptado (ADR-012): la cifra de prensa (-8,3 °C) menos
#     delta_brote_c (2 °C), porque se presume que la prensa informó nivel del cultivo.
NOCHE_EXTREMA = {
    "finca_id": "F-SR",
    "inicio": datetime(2026, 10, 5, 6, 0, tzinfo=timezone.utc),
    "fin": datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc),
    "minimo_c": -6.3,
}


def documentos(umbrales=None) -> list[dict]:
    """El documento de configuración. `umbrales` reemplaza a los de umbrales_riego.py (para pruebas)."""
    umbrales = umbrales if umbrales is not None else umbrales_riego.UMBRALES_RIEGO
    if umbrales is None:
        raise RuntimeError(
            "Faltan los umbrales de riego (db/seeds/umbrales_riego.py: UMBRALES_RIEGO es None). "
            "Hay que verificarlos con la Tabla 19 de la FAO-56 antes de cargar `configuracion`."
        )
    return [{
        "_id": "general",
        "delta_brote_c": 2,                    # Δ entre sensor y brote. Supuesto, ADR-005 (configurable)
        "nodo_inactivo_min": 30,               # minutos sin lecturas para considerar inactivo un nodo
        "sospechoso_minimo_c": {               # récord de septiembre de las normales 1991-2020 del SMN
            "san_rafael": -4.5,                # San Rafael Aero (verificacion-fuentes.md, sección 1)
            "san_martin": -2.8,                # San Martín
            "tupungato": -5.6,                 # sin estación del SMN: supuesto adoptado (ADR-012, decisión 2)
        },
        "noche_extrema": NOCHE_EXTREMA,
        "riesgo": {                            # cortes del índice de riesgo, adaptados de la FAO (ADR-005)
            "margen_bajo_c": 2, "margen_alto_c": 0, "horas_duracion": 2,
            "margen_duracion_c": 1, "aire_seco_pct": 60,
        },
        "umbrales_riego": umbrales,
    }]
