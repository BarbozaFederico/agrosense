"""Formato de textos y piezas HTML que comparten las pantallas del dashboard (ADR-018 y ADR-019).

Sin Streamlit ni MongoDB: son funciones puras, para poder probarlas solas.
"""

from datetime import date, datetime

ESTADO_TEXTO = {"helada": "Helada", "atencion": "Atención", "normal": "Sin helada", "sin_umbral": "Sin umbral"}
ESTADO_FORMA = {   # una forma distinta por estado, para no depender solo del color
    "helada": '<path d="M7 1 13 7 7 13 1 7Z" fill="currentColor"/>',
    "atencion": '<path d="M7 1.5 13 12.5H1Z" fill="currentColor"/>',
    "normal": '<circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="2"/>',
    "sin_umbral": '<path d="M2 7h10" stroke="currentColor" stroke-width="2"/>',
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
AGRAVANTES = {"duracion": "larga duración", "aire_seco": "aire seco", "suelo_seco": "suelo seco"}


def grados(v: float | None) -> str:
    return "-" if v is None else f"{v:.1f}".replace("-", "−").replace(".", ",") + " °C"


def numero(v: float, decimales: int = 0) -> str:
    """Número con punto de miles y coma decimal (1.520.000 / 76,5)."""
    texto = f"{v:,.{decimales}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def duracion(horas: float) -> str:
    minutos = round(horas * 60)
    return f"{minutos // 60} h {minutos % 60:02d} min" if minutos >= 60 else f"{minutos} min"


def hora(d: datetime) -> str:
    return f"{d:%H:%M}"


def fecha_corta(d: date | datetime) -> str:
    return f"{d.day} de {MESES[d.month - 1][:3]}"


def noche_texto(d: date) -> str:
    previo = date.fromordinal(d.toordinal() - 1)
    if previo.month == d.month:
        return f"Noche del {previo.day} al {d.day} de {MESES[d.month - 1]} de {d.year}"
    return f"Noche del {previo.day} de {MESES[previo.month - 1]} al {d.day} de {MESES[d.month - 1]} de {d.year}"


TIPO_TEXTO = {"helada": "Helada", "riego": "Riego"}


def marca_tipo(tipo: str) -> str:
    """Marca de una alerta: la helada usa el rombo rojo del estado; el riego, el triángulo ámbar de 'atención'."""
    estado = "helada" if tipo == "helada" else "atencion"
    return (f'<span class="marca-estado {estado}"><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">'
            f'{ESTADO_FORMA[estado]}</svg>{TIPO_TEXTO.get(tipo, tipo)}</span>')


def marca(estado: str) -> str:
    return (f'<span class="marca-estado {estado}"><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">'
            f'{ESTADO_FORMA[estado]}</svg>{ESTADO_TEXTO[estado]}</span>')
