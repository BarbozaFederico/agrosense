"""Consultas de agrosense, todas en Python con `pymongo` (ADR-014).

    q1_horas_bajo_cero ... q10_riesgo_de_helada   las 10 consultas del proyecto (docs/consultas.md)
    comun                                          fechas, ventana de una noche, tablas y texto de mongosh
    auditoria_lecturas                             los dos ceros de ADR-007 y ADR-009
    probar_consultas                               prueba cada consulta contra un cálculo independiente

Se corren desde la raíz del repo, por ejemplo: python -m db.queries.q9_etapa_por_grados_dia --fecha 2026-10-05
"""
