"""Prueba de los 10 esquemas.

Pregunta: ¿cada esquema acepta los documentos válidos y rechaza los inválidos?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.schemas.probar_esquemas

Usa la base de PRUEBA `agrosense_tests`, que se BORRA al empezar. No toca la base real.
Los datos son inventados, solo para probar.

Para cada colección común: inserta un documento válido (tiene que ENTRAR) y varios
inválidos (tienen que ser RECHAZADOS). Para `lecturas` (sin validador) prueba las
dos protecciones del ADR-007: el validador del simulador y la auditoría.
"""

import os
import subprocess
import sys
from datetime import datetime, timezone

from bson import ObjectId
from pymongo.errors import WriteError

from db.conexion import obtener_base, preparar_consola
from db.queries.auditoria_lecturas import auditar, contar_mal_formadas
from db.schemas import configuracion, lecturas
from db.schemas.crear import crear_colecciones
from db.schemas.validar import validar_documentos

ENTRA, RECHAZA = "ENTRA", "RECHAZADO"

# --- Datos de apoyo ---
FECHA = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)
POLIGONO = {"type": "Polygon", "coordinates": [[[-68.34, -34.62], [-68.32, -34.62], [-68.32, -34.60],
                                                [-68.34, -34.60], [-68.34, -34.62]]]}
PUNTO = {"type": "Point", "coordinates": [-68.33, -34.61]}
UMBRALES = {"sep_oct": 21, "nov": 21.5, "dic_ene": 18.5, "feb_mar": 20}


def sin(doc: dict, campo: str) -> dict:
    """Copia del documento sin ese campo."""
    return {k: v for k, v in doc.items() if k != campo}


def con(doc: dict, **cambios) -> dict:
    """Copia del documento con campos cambiados o agregados."""
    return {**doc, **cambios}


# --- Documentos válidos de cada colección ---
FINCA = {"_id": "F-SR", "nombre": "Finca de prueba", "departamento": "San Rafael", "oasis": "Sur",
         "altitud_m": 751, "geometria": POLIGONO, "sistema_riego": "surco", "tipo_suelo": "franco",
         "ficticia": True}
PARCELA = {"_id": "P-SR-1", "finca_id": "F-SR", "nombre": "Cuartel 1", "variedad_id": "malbec",
           "superficie_ha": 2, "geometria": POLIGONO, "conduccion": "espaldero", "densidad_plantas_ha": 4000}
NODO = {"_id": "N-SR-1-A", "parcela_id": "P-SR-1", "finca_id": "F-SR", "ubicacion": PUNTO,
        "estado": "activo", "instalado": FECHA,
        "variables": ["temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"]}
ALERTA = {"tipo": "helada", "parcela_id": "P-SR-1", "estado": "cerrada", "inicio": FECHA, "fin": FECHA,
          "etapa_bbch": 9, "umbral": -3.9, "valor_extremo": -4.3,
          "riesgo": {"nivel": "alto", "margen_c": -0.4, "agravantes": ["duracion"]}, "fuente": "simulado"}
ALERTA_ABIERTA = con(ALERTA, estado="abierta", fin=None, riesgo=None)
RIEGO = {"parcela_id": "P-SR-1", "inicio": FECHA, "fin": FECHA, "sistema": "surco", "origen": "turno",
         "lamina_mm": 76, "litros": 1520000, "fuente": "simulado"}
EVENTO = {"tipo": "helada", "inicio": FECHA, "fin": FECHA, "area": POLIGONO,
          "temperatura_minima_c": -4.5, "fuente": "seed"}
OBSERVACION = {"parcela_id": "P-SR-1", "fecha": FECHA, "etapa_bbch": 9, "observador": "tecnico", "fuente": "seed"}
VARIEDAD = {"_id": "malbec", "nombre": "Malbec", "ficticia": False,
            "grados_dia": {"base_c": 10, "tope_c": 32, "inicio": {"mes": 9, "dia": 1}, "hasta_brotacion": 70},
            "etapas": [{"bbch_desde": 7, "bbch_hasta": 9, "nombre": "Brotación", "baggiolini": "C",
                        "umbral_helada_c": -3.9, "gd_desde_brotacion": 0}]}
# Noche extrema de prueba (ADR-009): 5/10/2026 de 06:00 a 11:00 UTC (03:00 a 08:00 en Argentina).
NOCHE_INICIO = datetime(2026, 10, 5, 6, 0, tzinfo=timezone.utc)
NOCHE_FIN = datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)
NOCHE_EXTREMA = {"finca_id": "F-SR", "inicio": NOCHE_INICIO, "fin": NOCHE_FIN, "minimo_c": -6.3}
CONFIGURACION = {"_id": "general", "delta_brote_c": 2, "nodo_inactivo_min": 30,
                 "sospechoso_minimo_c": {"san_rafael": -4.5, "san_martin": -2.8, "tupungato": None},
                 "noche_extrema": NOCHE_EXTREMA,
                 "riesgo": {"margen_bajo_c": 2, "margen_alto_c": 0, "horas_duracion": 2,
                            "margen_duracion_c": 1, "aire_seco_pct": 60},
                 "umbrales_riego": {"franco": UMBRALES, "franco_arenoso": UMBRALES, "pedregoso": UMBRALES}}

# --- Casos: (colección, descripción, documento, resultado esperado) ---
CASOS = [
    ("fincas", "Válido", FINCA, ENTRA),
    ("fincas", "Código con formato incorrecto (_id: 'finca1')", con(FINCA, _id="finca1"), RECHAZA),
    ("fincas", "Departamento fuera de la lista", con(FINCA, _id="F-XX", departamento="Maipú"), RECHAZA),
    ("fincas", "Campo de más (propietario)", con(FINCA, _id="F-YY", propietario="x"), RECHAZA),

    ("parcelas", "Válido", PARCELA, ENTRA),
    ("parcelas", "Superficie 0 (tiene que ser mayor que 0)", con(PARCELA, _id="P-SR-2", superficie_ha=0), RECHAZA),
    ("parcelas", "Geometría que no es polígono", con(PARCELA, _id="P-SR-3", geometria=PUNTO), RECHAZA),

    ("nodos", "Válido", NODO, ENTRA),
    ("nodos", "Estado fuera de la lista ('reportando')", con(NODO, _id="N-SR-1-B", estado="reportando"), RECHAZA),
    ("nodos", "Variable repetida en la lista", con(NODO, _id="N-SR-1-C", variables=["temperatura_c", "temperatura_c"]), RECHAZA),

    ("alertas", "Válido: helada cerrada con riesgo", ALERTA, ENTRA),
    ("alertas", "Válido: alerta abierta (fin y riesgo en None)", ALERTA_ABIERTA, ENTRA),
    ("alertas", "Abierta pero con fecha de fin", con(ALERTA_ABIERTA, fin=FECHA), RECHAZA),
    ("alertas", "Cerrada sin fecha de fin", con(ALERTA, fin=None), RECHAZA),
    ("alertas", "Alerta de riego con riesgo", con(ALERTA, tipo="riego"), RECHAZA),
    ("alertas", "Nivel de riesgo fuera de la lista",
     con(ALERTA, riesgo={"nivel": "extremo", "margen_c": -1, "agravantes": []}), RECHAZA),

    ("riegos", "Válido: riego por turno", RIEGO, ENTRA),
    ("riegos", "Válido: riego por alerta con alerta_id", con(RIEGO, origen="alerta", alerta_id=ObjectId()), ENTRA),
    ("riegos", "Riego por alerta sin alerta_id", con(RIEGO, origen="alerta"), RECHAZA),
    ("riegos", "Litros negativos", con(RIEGO, litros=-5), RECHAZA),
    ("riegos", "Falta lamina_mm", sin(RIEGO, "lamina_mm"), RECHAZA),

    ("eventos_climaticos", "Válido", EVENTO, ENTRA),
    ("eventos_climaticos", "Tipo fuera de la lista ('tornado')", con(EVENTO, tipo="tornado"), RECHAZA),
    ("eventos_climaticos", "Tipo 'granizo' (fuera de alcance)", con(EVENTO, tipo="granizo"), RECHAZA),

    ("observaciones_fenologicas", "Válido", OBSERVACION, ENTRA),
    ("observaciones_fenologicas", "Etapa BBCH fuera de rango (120)", con(OBSERVACION, etapa_bbch=120), RECHAZA),
    ("observaciones_fenologicas", "Observador con nombre de persona", con(OBSERVACION, observador="Juan Pérez"), RECHAZA),

    ("variedades", "Válido", VARIEDAD, ENTRA),
    ("variedades", "Etapa con un campo de más",
     con(VARIEDAD, _id="otra", etapas=[{**VARIEDAD["etapas"][0], "color": "verde"}]), RECHAZA),
    ("variedades", "Mes de inicio inválido (13)",
     con(VARIEDAD, _id="otra2", grados_dia={**VARIEDAD["grados_dia"], "inicio": {"mes": 13, "dia": 1}}), RECHAZA),

    ("configuracion", "Válido", CONFIGURACION, ENTRA),
    ("configuracion", "_id distinto de 'general'", con(CONFIGURACION, _id="otra"), RECHAZA),
    ("configuracion", "Falta sospechoso_minimo_c", sin(CONFIGURACION, "sospechoso_minimo_c"), RECHAZA),
    ("configuracion", "Falta la clave tupungato (tiene que ser None, no faltar)",
     con(CONFIGURACION, sospechoso_minimo_c={"san_rafael": -4.5, "san_martin": -2.8}), RECHAZA),
    ("configuracion", "Valor de texto en sospechoso_minimo_c",
     con(CONFIGURACION, sospechoso_minimo_c={"san_rafael": "frio", "san_martin": -2.8, "tupungato": None}), RECHAZA),
    ("configuracion", "Clave con tilde ('San Martín')",
     con(CONFIGURACION, sospechoso_minimo_c={"san_rafael": -4.5, "San Martín": -2.8, "tupungato": None}), RECHAZA),
    ("configuracion", "Límite de frío positivo (san_rafael = 1.0)",
     con(CONFIGURACION, sospechoso_minimo_c={"san_rafael": 1.0, "san_martin": -2.8, "tupungato": None}), RECHAZA),
    ("configuracion", "Falta noche_extrema", sin(CONFIGURACION, "noche_extrema"), RECHAZA),
    ("configuracion", "noche_extrema con minimo_c positivo",
     con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "minimo_c": 3}), RECHAZA),
    ("configuracion", "noche_extrema con finca_id de formato incorrecto",
     con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "finca_id": "finca1"}), RECHAZA),
    ("configuracion", "noche_extrema con la fecha de inicio como texto",
     con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "inicio": "2026-10-05"}), RECHAZA),
    ("configuracion", "noche_extrema con un campo de más",
     con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "notas": "x"}), RECHAZA),
    ("configuracion", "Porcentaje mayor que 100",
     con(CONFIGURACION, riesgo={**CONFIGURACION["riesgo"], "aire_seco_pct": 150}), RECHAZA),
]

# --- Lecturas de prueba: 1 válida y 3 inválidas ---
META = {"nodo_id": "N-SR-1-A", "parcela_id": "P-SR-1", "finca_id": "F-SR", "fuente": "simulado"}
LECTURA = {"ts": FECHA, "meta": META, "temperatura_c": -1.8, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81}
LECTURAS = [
    LECTURA,                                                      # válida
    con(LECTURA, x=1),                                            # campo de más
    con(LECTURA, temperatura_c=500),                              # temperatura imposible
    con(LECTURA, meta={**META, "nodo_id": "nodo1"}),              # código mal
]


def probar_insercion(bd, coleccion: str, doc: dict) -> str:
    """Intenta insertar y devuelve ENTRA o RECHAZADO.

    Se inserta una copia porque insert_one le agrega _id al diccionario.
    """
    try:
        bd[coleccion].insert_one(dict(doc))
        return ENTRA
    except WriteError:                # el validador rechazó el documento
        return RECHAZA


class Resumen:
    """Cuenta los casos y las fallas, y muestra cada resultado."""

    def __init__(self) -> None:
        self.total = 0
        self.fallas = 0

    def chequear(self, ok: bool, texto: str) -> None:
        self.total += 1
        self.fallas += not ok
        print(f"{'✔' if ok else '✘ INESPERADO'} | {texto}")


def lectura(finca: str, ts: datetime, temperatura: float) -> dict:
    """Una lectura válida de la finca indicada (F-SR → nodo N-SR-1-A, parcela P-SR-1)."""
    sufijo = finca.split("-")[1]
    meta = {"nodo_id": f"N-{sufijo}-1-A", "parcela_id": f"P-{sufijo}-1", "finca_id": finca, "fuente": "simulado"}
    return {"ts": ts, "meta": meta, "temperatura_c": temperatura, "humedad_suelo_pct": 23.4, "humedad_aire_pct": 81}


def codigo_de_salida_de_la_auditoria() -> int:
    """Corre la auditoría como script (sobre agrosense_tests) y devuelve su código de salida."""
    entorno = {**os.environ, "AGROSENSE_BD": "agrosense_tests"}
    proceso = subprocess.run([sys.executable, "-m", "db.queries.auditoria_lecturas"],
                             env=entorno, capture_output=True)
    return proceso.returncode


def main() -> None:
    preparar_consola()
    bd = obtener_base("agrosense_tests")
    bd.client.drop_database("agrosense_tests")
    print(f"Versión del servidor: {bd.client.server_info()['version']} | base: agrosense_tests")

    print("--- Crear colecciones")
    crear_colecciones(bd)

    r = Resumen()
    print("--- Probar colecciones comunes (con validador)")
    for coleccion, descripcion, doc, esperado in CASOS:
        obtenido = probar_insercion(bd, coleccion, doc)
        r.chequear(obtenido == esperado, f"{coleccion} | {descripcion} | {obtenido}")

    # `configuracion` solo admite el _id "general": no se puede insertar dos veces. Este caso
    # se prueba con el validador sin guardar (db/schemas/validar.py): Tupungato con un valor numérico.
    con_valor = con(CONFIGURACION, sospechoso_minimo_c={"san_rafael": -4.5, "san_martin": -2.8, "tupungato": -5})
    validos, _ = validar_documentos(bd, configuracion.ESQUEMA, [con_valor])
    r.chequear(len(validos) == 1, "configuracion | Válido: Tupungato con valor numérico en vez de None | "
                                  "VÁLIDO (validado sin guardar)")

    print("--- Reglas de coherencia de configuracion (las que el esquema no puede expresar)")
    departamento_de_finca = {"F-SR": "san_rafael", "F-SM": "san_martin", "F-TU": "tupungato"}
    imposible = lecturas.ESQUEMA["properties"]["temperatura_c"]["minimum"]   # hoy -40, provisional
    coherencia = [
        ("Configuración coherente", CONFIGURACION, None),
        ("Límite de San Martín más frío que lo imposible (-50)",
         con(CONFIGURACION, sospechoso_minimo_c={"san_rafael": -4.5, "san_martin": -50, "tupungato": None}),
         "mínimo imposible"),
        ("Ventana con inicio posterior al fin",
         con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "inicio": NOCHE_FIN, "fin": NOCHE_INICIO}),
         "inicio tiene que ser anterior"),
        ("Piso de la noche extrema más cálido que el límite (-4,0 frente a -4,5)",
         con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "minimo_c": -4.0}), "más frío que"),
        ("Noche extrema en Tupungato, que no tiene límite",
         con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "finca_id": "F-TU"}), "no tiene límite"),
        ("Noche extrema en una finca que no existe",
         con(CONFIGURACION, noche_extrema={**NOCHE_EXTREMA, "finca_id": "F-XX"}), "ninguna finca"),
    ]
    for descripcion, config, texto_esperado in coherencia:
        errores = configuracion.verificar_coherencia(config, departamento_de_finca, imposible)
        ok = (errores == []) if texto_esperado is None else (len(errores) == 1 and texto_esperado in errores[0])
        r.chequear(ok, f"coherencia | {descripcion} | {'sin errores' if not errores else errores[0]}")

    print("--- Probar lecturas (serie temporal: validador del simulador y auditoría)")
    # 1) Validador del simulador: MongoDB valida sin guardar (db/schemas/validar.py).
    validos, invalidos = validar_documentos(bd, lecturas.ESQUEMA, LECTURAS)
    r.chequear((len(validos), len(invalidos)) == (1, 3) and validos[0] is LECTURAS[0],
               f"lecturas | validar_documentos con 4 lecturas: {len(validos)} válida y {len(invalidos)} "
               "inválidas (esperado: 1 y 3)")
    r.chequear("lecturas" in bd.list_collection_names() and bd.lecturas.count_documents({}) == 0,
               f"lecturas | validar no guardó nada ({bd.lecturas.count_documents({})} documentos en la colección)")

    # 2) Auditoría: se insertan las 4 SIN validar (como si alguien saltara el simulador).
    bd.lecturas.insert_many([dict(d) for d in LECTURAS])
    mal_formadas = contar_mal_formadas(bd)
    r.chequear(mal_formadas == 3, f"lecturas | 4 insertadas sin validar: la auditoría encontró "
                                  f"{mal_formadas} mal formadas (esperado: 3)")

    print("--- Auditoría de lecturas sospechosas (ADR-009)")
    # Se parte de una colección limpia y se cargan fincas de los tres departamentos.
    bd.lecturas.delete_many({})
    bd.fincas.insert_many([con(FINCA, _id="F-SM", departamento="San Martín", oasis="Este"),
                           con(FINCA, _id="F-TU", departamento="Tupungato", oasis="Valle de Uco")])
    fuera = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)      # fuera de la noche extrema
    dentro = datetime(2026, 10, 5, 8, 0, tzinfo=timezone.utc)     # dentro de la ventana
    bd.lecturas.insert_many([
        lectura("F-SR", fuera, -3.0),     # normal (más cálida que -4,5)
        lectura("F-SR", fuera, -4.5),     # justo en el límite: NO es sospechosa (es estrictamente menor)
        lectura("F-SR", fuera, -5.0),     # sospechosa INESPERADA: fuera de la noche extrema
        lectura("F-SR", dentro, -5.5),    # sospechosa esperada
        lectura("F-SR", dentro, -6.0),    # sospechosa esperada
        lectura("F-SR", dentro, -6.3),    # sospechosa esperada: justo en el piso
        lectura("F-SR", dentro, -6.8),    # sospechosa INESPERADA: más fría que el piso
        lectura("F-SM", fuera, -2.0),     # normal
        lectura("F-SM", dentro, -3.5),    # sospechosa INESPERADA: la excepción es solo de F-SR
        lectura("F-TU", fuera, -10.0),    # Tupungato no tiene límite: no se audita como sospechosa
    ])
    a = auditar(bd)
    r.chequear(a["mal_formadas"] == 0, f"auditoría | mal formadas: {a['mal_formadas']} (esperado: 0)")
    r.chequear(a["esperadas"] == 3 and a["minima_esperada"] == -6.3,
               f"auditoría | esperadas: {a['esperadas']} y la más fría {a['minima_esperada']} (esperado: 3 y -6,3)")
    r.chequear(a["inesperadas"] == 3,
               f"auditoría | inesperadas: {a['inesperadas']} (esperado: 3: fuera de la noche, bajo el piso, otra finca)")
    r.chequear(a["sin_limite"] == ["F-TU"], f"auditoría | sin límite (no auditadas): {a['sin_limite']} (esperado: F-TU)")
    r.chequear(not a["aprobada"], f"auditoría | con inesperadas no aprueba (aprobada: {a['aprobada']})")
    r.chequear(codigo_de_salida_de_la_auditoria() == 1, "auditoría | como script termina con error (código 1)")

    # Se borran las 3 inesperadas y la auditoría tiene que aprobar, con las 3 esperadas informadas.
    bd.lecturas.delete_many({"temperatura_c": {"$in": [-5.0, -6.8]}})
    bd.lecturas.delete_many({"meta.finca_id": "F-SM", "temperatura_c": -3.5})
    a = auditar(bd)
    r.chequear(a["aprobada"] and a["esperadas"] == 3 and a["inesperadas"] == 0,
               f"auditoría | sin inesperadas aprueba (aprobada: {a['aprobada']}, esperadas: {a['esperadas']})")
    r.chequear(codigo_de_salida_de_la_auditoria() == 0, "auditoría | como script termina bien (código 0)")

    # Sin documento de configuración no se pueden auditar las sospechosas: se avisa, no se falla.
    bd.configuracion.delete_many({})
    a = auditar(bd)
    r.chequear(a["config_faltante"] and a["mal_formadas"] == 0,
               f"auditoría | sin configuración: avisa y audita solo el formato (config_faltante: {a['config_faltante']})")

    print("---")
    print(f"RESULTADO: todos los casos dieron lo esperado ({r.total} casos)" if r.fallas == 0
          else f"RESULTADO: {r.fallas} de {r.total} casos NO dieron lo esperado")


if __name__ == "__main__":
    main()
