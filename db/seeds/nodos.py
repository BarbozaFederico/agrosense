"""Datos de `nodos` (12, dos por parcela). Esquema: db/schemas/nodos.py.

Todos miden las 3 variables del MVP. Se instalan antes del inicio de la temporada
(1/9/2026), con la fecha en UTC.
"""

from datetime import datetime, timezone

from db.seeds.ubicaciones import PARCELAS_DE_FINCA, ubicacion_nodo

NOMBRE = "nodos"

INSTALADO = datetime(2026, 8, 1, tzinfo=timezone.utc)
VARIABLES = ["temperatura_c", "humedad_suelo_pct", "humedad_aire_pct"]


def documentos() -> list[dict]:
    docs = []
    for finca_id, parcelas in PARCELAS_DE_FINCA.items():
        for parcela_id in parcelas:
            for letra in ("A", "B"):
                nodo_id = f"N-{parcela_id[2:]}-{letra}"            # P-SR-1 → N-SR-1-A
                docs.append({
                    "_id": nodo_id, "parcela_id": parcela_id, "finca_id": finca_id,
                    "ubicacion": ubicacion_nodo(nodo_id), "estado": "activo",
                    "instalado": INSTALADO, "variables": list(VARIABLES),
                })
    return docs
