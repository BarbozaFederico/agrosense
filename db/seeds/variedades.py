"""Datos de `variedades`: el Malbec con sus etapas BBCH. Esquema: db/schemas/variedades.py.

Decisión 3 del ADR-010: las etapas cubren BBCH 0 a 99 sin huecos, para que Q9 siempre
devuelva una etapa. Las etapas sin umbral con fuente llevan `umbral_helada_c: None`
(no se evalúan: no se inventa un umbral).

`gd_desde_brotacion` son los grados-día (base 10 °C) desde la brotación a los que
empieza la etapa. Negativo: antes de la brotación. Marca de cada valor:

    con fuente   260 (floración, BBCH 65) y 972 = 260 + 712 (envero, BBCH 81):
                 Zapata et al. 2017, Tabla 5 (verificacion-fuentes.md, sección 8).
    supuesto     el resto. Salen de la tabla de vid-malbec.md (una etapa empieza en el
                 valor que ahí tiene su primer código) y, cuando el primer código de la
                 etapa no está en esa tabla, de una interpolación lineal entre los dos
                 códigos vecinos. Se corrigen con las observaciones manuales (ADR-004).

Los 70 grados-día desde el 1/9 hasta la brotación son supuesto (calibrado con la fecha
de Chacras de Coria, vid-malbec.md). El corte a la mitad (35) entre yema dormida e
hinchada es otro supuesto: ADR-010, decisión 3.

Umbrales (temperatura del brote, ADR-005): WSU EB1615 (Concord) para BBCH 0 a 15,
Ferguson et al. 2014 para racimos visibles y FDF / INIA 2016 para floración y cuaje.
"""

NOMBRE = "variedades"

HASTA_BROTACION_GD = 70
CORTE_YEMA_GD = HASTA_BROTACION_GD / 2     # 35: yema dormida hasta acá, hinchada desde acá

# bbch_desde, bbch_hasta, nombre, baggiolini, umbral_helada_c, gd_desde_brotacion
ETAPAS_MALBEC = [
    (0, 0, "Yema dormida", "A", -10.6, -HASTA_BROTACION_GD),
    (1, 6, "Yema hinchada", "B", -6.1, -CORTE_YEMA_GD),
    (7, 10, "Brotación", "C", -3.9, 0),
    (11, 11, "Primera hoja", "D", -2.8, 30),
    (12, 15, "2 a 5 hojas", "E", -2.2, 42.5),          # 42,5: interpolado entre BBCH 11 (30) y 15 (80)
    (16, 52, "Hojas desplegadas", "E-F", None, 80.8),  # sin umbral con fuente; interpolado entre 15 y 53
    (53, 57, "Racimos visibles", "F-H", -1.2, 110),
    (58, 59, "Botones separados", "H", None, 200),     # sin umbral con fuente; interpolado entre 57 y 61
    (60, 71, "Floración y cuaje", "I-J", 0, 220),      # 220: interpolado; BBCH 65 (260) con fuente
    (72, 76, "Fruto pequeño", "J-K", None, 375),       # interpolado entre 71 (330) y 77 (600)
    (77, 80, "Cierre del racimo", "L", None, 600),
    (81, 88, "Envero y maduración", "M", None, 972),   # con fuente: 260 + 712 (Zapata 2017)
    (89, 99, "Madurez", "N", None, 1450),              # supuesto: 1.450 a 1.700 en vid-malbec.md
]


def verificar_etapas(etapas: list[dict]) -> list[str]:
    """Reglas que el esquema no puede expresar. Devuelve los errores (vacía si todo bien):
    las etapas cubren BBCH 0 a 99 sin huecos ni superposiciones, ordenadas, y los
    grados-día crecen de una etapa a la siguiente."""
    errores = []
    esperado = 0
    gd_anterior = None
    for etapa in etapas:
        if etapa["bbch_desde"] != esperado:
            errores.append(f"{etapa['nombre']}: empieza en BBCH {etapa['bbch_desde']} y debería "
                           f"empezar en {esperado} (hueco o superposición)")
        if etapa["bbch_hasta"] < etapa["bbch_desde"]:
            errores.append(f"{etapa['nombre']}: bbch_hasta menor que bbch_desde")
        gd = etapa["gd_desde_brotacion"]
        if gd_anterior is not None and gd <= gd_anterior:
            errores.append(f"{etapa['nombre']}: los grados-día ({gd}) tienen que superar a los de la etapa anterior ({gd_anterior})")
        gd_anterior = gd
        esperado = etapa["bbch_hasta"] + 1
    if esperado != 100:
        errores.append(f"las etapas terminan en BBCH {esperado - 1} y deberían llegar a 99")
    return errores


def documentos() -> list[dict]:
    etapas = [
        {"bbch_desde": desde, "bbch_hasta": hasta, "nombre": nombre, "baggiolini": baggiolini,
         "umbral_helada_c": umbral, "gd_desde_brotacion": gd}
        for desde, hasta, nombre, baggiolini, umbral, gd in ETAPAS_MALBEC
    ]
    return [{
        "_id": "malbec", "nombre": "Malbec", "ficticia": False,
        "grados_dia": {"base_c": 10, "tope_c": 32, "inicio": {"mes": 9, "dia": 1},
                       "hasta_brotacion": HASTA_BROTACION_GD},
        "etapas": etapas,
    }]
