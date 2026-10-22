"""agrosense - dashboard (ADR-002, ADR-018 y ADR-019).

Solo arma el menú y el estilo; cada pantalla vive en `paginas/`. Se corre desde la raíz del repo:
    python -m streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # para importar `db` y `dashboard` desde la raíz

from dashboard.estilo import CSS                # noqa: E402

st.set_page_config(page_title="agrosense", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
pagina = st.navigation([
    st.Page("paginas/resumen.py", title="Resumen de la mañana", url_path="resumen", default=True),
    st.Page("paginas/detalle.py", title="Detalle de parcela", url_path="detalle"),
], position="hidden")                                # el menú lo dibuja `lateral.py`, con las pantallas pendientes
pagina.run()
