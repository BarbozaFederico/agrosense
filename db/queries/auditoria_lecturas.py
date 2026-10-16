"""Auditoría de `lecturas` (ADR-007 y ADR-009).

Responde dos preguntas después de cada carga:

1. ¿Hay lecturas que no cumplan el esquema de docs/modelo-datos.md (sección 3.4)?
   Por qué existe: `lecturas` es una serie temporal y MongoDB 9.0.2 no le permite tener
   validador. El mismo $jsonSchema sí funciona como FILTRO de búsqueda (spike de
   esquemas, prueba 3).

2. ¿Hay lecturas "sospechosas", es decir, más frías que el límite de su departamento
   (configuracion.sospechoso_minimo_c)? Se comparan contra `temperatura_c`, la lectura
   del sensor, y es sospechosa si es ESTRICTAMENTE menor que el límite. Pueden ser:
     - esperadas: dentro de la "noche extrema" declarada en configuracion.noche_extrema
       (esa finca, esa ventana) y sin pasar su piso (minimo_c);
     - inesperadas: todas las demás.
   Las lecturas sospechosas NO se rechazan ni se excluyen de las consultas: solo se cuentan.

Aprueba si mal formadas = 0 e inesperadas = 0. Las esperadas se informan aparte, y el
script termina con error (código 1) si falla alguno de los dos ceros.

Si un departamento no tiene límite (hoy, Tupungato) sus lecturas NO se auditan como
sospechosas: se avisa de forma visible, y no cuenta como falla (ADR-009).

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m db.queries.auditoria_lecturas
Para otra base (Git Bash):
    AGROSENSE_BD=agrosense_tests python -m db.queries.auditoria_lecturas
"""

import sys

from db.conexion import obtener_base, preparar_consola
from db.departamentos import clave_departamento
from db.schemas import lecturas

# $nor: [{ $jsonSchema }] significa "que NO cumpla el esquema".
FILTRO_MAL_FORMADAS = {"$nor": [{"$jsonSchema": lecturas.ESQUEMA}]}


def contar_mal_formadas(bd) -> int:
    """Cantidad de lecturas que no cumplen el esquema."""
    return bd.lecturas.count_documents(FILTRO_MAL_FORMADAS)


def auditar(bd) -> dict:
    """Corre la auditoría y devuelve los resultados (sin imprimir nada)."""
    resultado = {
        "total": bd.lecturas.count_documents({}),
        "mal_formadas": contar_mal_formadas(bd),
        "config_faltante": False,
        "esperadas": 0,
        "minima_esperada": None,     # la lectura más fría de la noche extrema
        "inesperadas": 0,
        "sin_limite": [],            # fincas cuyas lecturas no se pudieron auditar como sospechosas
    }

    config = bd.configuracion.find_one({"_id": "general"})
    if config is None:
        resultado["config_faltante"] = True
    else:
        limites = config["sospechoso_minimo_c"]
        noche = config["noche_extrema"]
        departamento_de_finca = {f["_id"]: clave_departamento(f["departamento"])
                                 for f in bd.fincas.find({}, {"departamento": 1})}

        for finca_id in sorted(bd.lecturas.distinct("meta.finca_id")):
            limite = limites.get(departamento_de_finca.get(finca_id))
            if limite is None:
                resultado["sin_limite"].append(finca_id)
                continue

            filtro_finca = {"meta.finca_id": finca_id}
            sospechosas = bd.lecturas.count_documents({**filtro_finca, "temperatura_c": {"$lt": limite}})
            esperadas = 0
            if finca_id == noche["finca_id"]:
                filtro_esperadas = {
                    **filtro_finca,
                    "temperatura_c": {"$lt": limite, "$gte": noche["minimo_c"]},   # sin pasar su piso
                    "ts": {"$gte": noche["inicio"], "$lte": noche["fin"]},         # dentro de la ventana
                }
                esperadas = bd.lecturas.count_documents(filtro_esperadas)
                if esperadas:
                    fria = bd.lecturas.find(filtro_esperadas).sort("temperatura_c", 1).limit(1)
                    resultado["minima_esperada"] = next(fria)["temperatura_c"]
            resultado["esperadas"] += esperadas
            resultado["inesperadas"] += sospechosas - esperadas

    resultado["aprobada"] = resultado["mal_formadas"] == 0 and resultado["inesperadas"] == 0
    return resultado


def main() -> None:
    preparar_consola()
    bd = obtener_base()
    r = auditar(bd)
    print(f"Base: {bd.name}")
    print(f"Lecturas totales: {r['total']}")
    print(f"Mal formadas (no cumplen el esquema): {r['mal_formadas']}  (esperado: 0)")
    if r["config_faltante"]:
        print("AVISO: no hay documento de configuración: las lecturas sospechosas NO se auditaron.")
    else:
        print(f"Sospechosas esperadas (noche extrema): {r['esperadas']}"
              + (f"  (la más fría: {r['minima_esperada']} °C)" if r["esperadas"] else ""))
        print(f"Sospechosas inesperadas: {r['inesperadas']}  (esperado: 0)")
        if r["sin_limite"]:
            print("AVISO: sin límite de sospechoso, NO auditadas como sospechosas: "
                  + ", ".join(r["sin_limite"]))
    if r["mal_formadas"]:
        print("Ejemplos de mal formadas (hasta 5):")
        for doc in bd.lecturas.find(FILTRO_MAL_FORMADAS).limit(5):
            print("  ", doc)
        # Para borrarlas (las series temporales permiten borrar con cualquier filtro):
        #     bd.lecturas.delete_many(FILTRO_MAL_FORMADAS)
    print("RESULTADO: " + ("APRUEBA" if r["aprobada"] else "FALLA"))
    if not r["aprobada"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
