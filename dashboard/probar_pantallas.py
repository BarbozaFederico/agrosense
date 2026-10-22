"""Prueba de las pantallas armadas, de punta a punta (ADR-019).

Pregunta: ¿las dos pantallas se abren sin errores con la base real de pruebas, con y sin parámetros en la URL, y los
controles (fecha, botones de noches, parcela) hacen lo que dicen?

Cómo correrlo (desde la raíz del repo, con el entorno virtual activado):
    python -m dashboard.probar_pantallas

Usa `streamlit.testing.v1.AppTest`: corre `dashboard/app.py` sin navegador, contra la base de PRUEBA `agrosense_tests`
(si está vacía, corré antes  python -m db.queries.probar_consultas). No escribe nada. Tarda unos segundos.
Los avisos "missing ScriptRunContext" que imprime Streamlit al correr sin servidor son normales.
"""

import os
import sys
from datetime import date
from pathlib import Path

os.environ["AGROSENSE_BD"] = "agrosense_tests"          # antes de que `dashboard.data` abra la conexión

from streamlit.testing.v1 import AppTest                 # noqa: E402

from db.conexion import preparar_consola                 # noqa: E402
from db.schemas.probar_esquemas import Resumen           # noqa: E402

APP = str(Path(__file__).resolve().parent / "app.py")
PARCELAS = ["P-SR-1", "P-SR-2", "P-SM-1", "P-SM-2", "P-TU-1", "P-TU-2"]


def abrir(pagina: str | None = None, **parametros) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=90)
    for k, v in parametros.items():
        at.query_params[k] = v
    if pagina:
        at.switch_page(pagina)
    return at.run()


def textos(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown)


def main() -> None:
    preparar_consola()
    r = Resumen()

    at = abrir(fecha="2026-10-05")
    r.chequear(not at.exception, "Resumen abre sin errores con la noche precargada")
    t = textos(at)
    r.chequear("2 de 4 parcelas bajaron de su umbral de helada" in t, "Resumen dice 2 de 4 parcelas el 5/10")
    r.chequear(t.count('class="enlace"') == 6 and "detalle?parcela=P-SR-1&fecha=2026-10-05" in t,
               "Resumen enlaza cada una de las 6 filas con su detalle y la fecha viaja en el enlace")
    r.chequear(at.sidebar.date_input[0].value == date(2026, 10, 5), "la fecha de la URL llega al selector de fecha")

    at = abrir(fecha="no-es-una-fecha")
    r.chequear(not at.exception and at.sidebar.date_input[0].value == date(2026, 10, 5), "una fecha mal escrita en la URL vuelve a la noche precargada")
    at = abrir(fecha="2030-01-01")
    r.chequear(not at.exception and at.sidebar.date_input[0].value == date(2026, 10, 5), "una fecha fuera de la temporada vuelve a la noche precargada")

    at = abrir(fecha="2026-10-08")
    r.chequear(not at.exception and "Ninguna parcela bajó de su umbral esta noche" in textos(at), "una noche sin helada (8/10) lo dice")
    at.sidebar.selectbox[0].set_value("F-SR").run()
    r.chequear(not at.exception and textos(at).count('class="enlace"') == 2, "el filtro de finca deja las 2 parcelas de esa finca")

    at = abrir(fecha="2026-10-05")
    at.sidebar.button[1].click().run()          # "29 de sep"
    r.chequear(not at.exception and at.sidebar.date_input[0].value == date(2026, 9, 29), "el botón de una noche con helada cambia la fecha")

    # ---- Detalle
    for parcela in PARCELAS:
        at = abrir("paginas/detalle.py", parcela=parcela, fecha="2026-10-05")
        t = textos(at)
        r.chequear(not at.exception and at.sidebar.selectbox[0].value == parcela and 'class="frase"' in t,
                   f"Detalle abre {parcela} el 5/10 sin errores y con la parcela elegida")
    at = abrir("paginas/detalle.py", parcela="P-SR-1", fecha="2026-10-05")
    t = textos(at)
    r.chequear("bajó a −8,3 °C en el brote, 4,4 °C bajo su umbral" in t and "Alerta de 02:05 a 08:40" in t,
               "Detalle de P-SR-1 dice la mínima, el margen y la alerta")
    r.chequear(len(at.sidebar.selectbox) == 1 and at.sidebar.selectbox[0].label == "Parcela", "Detalle muestra el selector de parcela (no el de finca)")
    at.sidebar.selectbox[0].set_value("P-TU-2").run()
    r.chequear(not at.exception and "Cuartel 2 · Finca Los Cipreses" in textos(at) and "N-TU-2-B está en mantenimiento" in textos(at),
               "cambiar de parcela redibuja el detalle y avisa del nodo en mantenimiento")
    at.sidebar.date_input[0].set_value(date(2026, 10, 8)).run()
    r.chequear(not at.exception and "no bajó de su umbral" in textos(at), "cambiar la fecha redibuja el detalle (8/10, sin helada)")

    at = abrir("paginas/detalle.py", parcela="P-NO-EXISTE", fecha="2026-10-05")
    r.chequear(not at.exception and at.sidebar.selectbox[0].value == "P-SR-1", "una parcela inexistente en la URL arranca en la de peor estado")
    at = abrir("paginas/detalle.py")
    r.chequear(not at.exception and at.sidebar.selectbox[0].value == "P-SR-1", "sin parámetros Detalle arranca en la parcela de peor estado de la noche precargada")

    for dia in ("2026-09-01", "2027-03-31"):
        at = abrir("paginas/detalle.py", parcela="P-SM-2", fecha=dia)
        r.chequear(not at.exception, f"Detalle abre sin errores en el borde de la temporada ({dia})")

    # ---- Alertas
    at = abrir("paginas/alertas.py", fecha="2026-10-05")
    t = textos(at)
    r.chequear(not at.exception and "2 alertas de helada esta noche, en Finca Los Álamos (San Rafael)" in t, "Alertas abre el 5/10 y dice 2 alertas de helada en San Rafael")
    r.chequear(t.count('class="enlace"') == 2 and "detalle?parcela=P-SR-1&fecha=2026-10-05" in t, "Alertas enlaza cada alerta de la noche con el detalle de su parcela")
    r.chequear("Semana del 5 de oct" in t and "semana elegida" in t, "Alertas muestra el resumen semanal con la semana elegida")
    r.chequear(len(at.dataframe) == 1, "Alertas muestra el historial como tabla ordenable")
    r.chequear(at.sidebar.selectbox[0].label == "Finca" and at.segmented_control[0].value == "Todas", "Alertas muestra el filtro de finca y el de tipo (Todas)")
    at.segmented_control[0].set_value("Riego").run()
    r.chequear(not at.exception and "No hubo alertas de riego esta noche" in textos(at), "el filtro Riego deja sin alertas la noche del 5/10")
    at.segmented_control[0].set_value("Helada").run()
    r.chequear(not at.exception and "2 alertas de helada" in textos(at), "el filtro Helada deja las 2 alertas")
    at.sidebar.selectbox[0].set_value("F-TU").run()
    r.chequear(not at.exception and "No hubo alertas de helada esta noche" in textos(at) and "Tupungato" in textos(at),
               "el filtro de finca (Tupungato) deja sin alertas esa noche y el resumen muestra solo su departamento")

    at = abrir("paginas/alertas.py", fecha="2026-11-17")
    r.chequear(not at.exception and "1 alerta de riego esta noche, en Finca Los Cipreses (Tupungato)" in textos(at), "una noche con alerta de riego (17/11) la muestra")
    at = abrir("paginas/alertas.py", fecha="2026-10-08")
    r.chequear(not at.exception and "No hubo alertas esta noche" in textos(at) and "Sin alertas con este filtro" in textos(at), "una noche sin alertas (8/10) muestra el estado vacío")
    at = abrir("paginas/alertas.py", fecha="2026-09-01")
    r.chequear(not at.exception and "Todavía no hay alertas en la temporada" in textos(at), "el primer día de la temporada no tiene historial y no se rompe")
    at = abrir("paginas/alertas.py", fecha="2027-03-31")
    r.chequear(not at.exception and "35</b> alertas en la temporada" in textos(at), "el último día la temporada suma las 35 alertas")
    at.sidebar.button[0].click().run()
    r.chequear(not at.exception and at.sidebar.date_input[0].value == date(2026, 9, 22), "el botón de una noche con helada cambia la fecha en Alertas")

    print(f"\n{r.total - r.fallas} de {r.total} casos pasaron.")
    sys.exit(1 if r.fallas else 0)


if __name__ == "__main__":
    main()
