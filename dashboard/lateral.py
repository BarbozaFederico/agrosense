"""Barra lateral común de las pantallas: navegación, selectores y la fecha (ADR-019).

La fecha es la "mañana de la noche" que se muestra (ADR-004 y ADR-018). Vive en `st.session_state` y en la URL
(`?fecha=2026-10-05`): las filas de la tabla del resumen enlazan al detalle con un ancla, que abre una sesión
nueva y entonces solo la URL sabe qué parcela y qué noche se estaban mirando.
"""

from datetime import date

import streamlit as st

from dashboard import data
from dashboard.formato import fecha_corta

FECHA_INICIAL = date(2026, 10, 5)               # la noche de helada precargada (RF-13)
TEMPORADA = (date(2026, 9, 1), date(2027, 3, 31))
PANTALLAS_HECHAS = [("paginas/resumen.py", "Resumen de la mañana"), ("paginas/detalle.py", "Detalle de parcela")]
PANTALLAS_PENDIENTES = ["Alertas", "Estado de nodos"]


def fecha_de_la_url() -> date | None:
    """La fecha de `?fecha=AAAA-MM-DD`, o None si falta, está mal escrita o cae fuera de la temporada."""
    try:
        d = date.fromisoformat(st.query_params.get("fecha", ""))
    except ValueError:
        return None
    return d if TEMPORADA[0] <= d <= TEMPORADA[1] else None


def _ir_a(dia: date) -> None:
    st.session_state["fecha"] = dia


def barra_lateral(con_finca: bool = False, con_parcela: bool = False) -> str | None:
    """Dibuja la barra lateral y devuelve la finca o la parcela elegida (None = todas las fincas)."""
    if "fecha" not in st.session_state:
        st.session_state["fecha"] = fecha_de_la_url() or FECHA_INICIAL
    elegido = None
    with st.sidebar:
        st.markdown('<div class="marca">agrosense <span>· viñedos</span></div>', unsafe_allow_html=True)
        for ruta, titulo in PANTALLAS_HECHAS:
            st.page_link(ruta, label=titulo)
        st.markdown('<ul class="nav">' + "".join(f"<li>{t}<small>en construcción</small></li>" for t in PANTALLAS_PENDIENTES)
                    + "</ul>", unsafe_allow_html=True)
        resumen = data.resumen(st.session_state["fecha"])
        if con_finca:
            nombres = {f["_id"]: f"{f['nombre']} · {f['departamento']}" for f in resumen["catalogo"]["fincas"]}
            elegido = st.selectbox("Finca", [None, *nombres],
                                   format_func=lambda k: "Todas las fincas" if k is None else nombres[k])
        if con_parcela:
            elegido = _selector_de_parcela(resumen)
        st.date_input("Mañana de la noche", min_value=TEMPORADA[0], max_value=TEMPORADA[1], key="fecha",
                      format="DD/MM/YYYY",
                      help="Define la noche que se muestra: de las 18:00 del día anterior a las 12:00 de esta fecha.")
        st.query_params["fecha"] = st.session_state["fecha"].isoformat()
        st.caption("Noches con alerta de helada")
        for i, dia in enumerate(data.noches_con_helada()):
            st.button(fecha_corta(dia), key=f"noche{i}", on_click=_ir_a, args=(dia,),
                      type="primary" if dia == st.session_state["fecha"] else "secondary", width="stretch")
        st.markdown('<span class="etiqueta-sim">datos simulados</span>', unsafe_allow_html=True)
    return elegido


def _selector_de_parcela(resumen: dict) -> str:
    """Selector de parcela: arranca en la de la URL (`?parcela=P-SR-1`) o, si no hay, en la de peor estado."""
    fincas = {f["_id"]: f["nombre"] for f in resumen["catalogo"]["fincas"]}
    parcelas = {p["_id"]: f"{p['nombre']} · {fincas[p['finca_id']]}" for p in resumen["catalogo"]["parcelas"]}
    if st.session_state.get("parcela") not in parcelas:
        de_la_url = st.query_params.get("parcela")
        st.session_state["parcela"] = de_la_url if de_la_url in parcelas else resumen["filas"][0]["parcela_id"]
    elegida = st.selectbox("Parcela", list(parcelas), format_func=parcelas.get, key="parcela")
    st.query_params["parcela"] = elegida
    return elegida
