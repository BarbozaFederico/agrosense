"""Estilo del dashboard: paleta del 'Boletín agrometeorológico' (ADR-018) y CSS de la pantalla.

Los colores de estado (helada, atención, normal) son los únicos de la paleta: el resto es grafito y
tinta cálida. El estado nunca va solo en color: cada fila lleva además una forma y una palabra.
"""

COLORES = {
    "fondo": "#14161a", "panel": "#1b1e23", "costura": "#2d3138", "pista": "#262a31",
    "tinta": "#ece6d8", "tinta_2": "#a9a597",
    "helada": "#ff7a6b", "atencion": "#f0b84a", "normal": "#6cc496", "neutro": "#8c8f95",
}

CSS = """
<style>
:root{--fondo:#14161a;--panel:#1b1e23;--costura:#2d3138;--pista:#262a31;--tinta:#ece6d8;--tinta-2:#a9a597;
--helada:#ff7a6b;--atencion:#f0b84a;--normal:#6cc496;--neutro:#8c8f95;
--ease:cubic-bezier(.22,1,.36,1)}
.stApp{background:var(--fondo);color:var(--tinta)}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:2.2rem;padding-bottom:3rem;max-width:1500px;padding-left:2rem;padding-right:2rem}
::selection{background:rgba(240,184,74,.35);color:var(--tinta)}
*{scrollbar-color:var(--costura) transparent;scrollbar-width:thin}
:focus-visible{outline:2px solid var(--atencion)!important;outline-offset:2px}
section[data-testid="stSidebar"]{width:15.5rem!important;min-width:15.5rem!important}
[data-testid="stSidebar"]{background:var(--panel);border-right:1px solid var(--costura)}
[data-testid="stSidebar"] .block-container{padding-top:1.4rem}
.marca{font-weight:700;font-size:1.15rem;letter-spacing:.01em;margin-bottom:.7rem}
.marca span{color:var(--tinta-2);font-weight:400}
.nav{list-style:none;margin:.15rem 0 1.2rem;padding:0}
.nav li{padding:.45rem .6rem;border-radius:4px;font-size:.92rem;color:var(--tinta-2)}
.nav li.activa{background:var(--pista);color:var(--tinta);font-weight:600}
.nav li small{display:block;font-size:.72rem;color:var(--neutro)}
.etiqueta-sim{display:inline-block;border:1px solid var(--costura);border-radius:3px;padding:.15rem .5rem;
font-size:.74rem;letter-spacing:.04em;text-transform:uppercase;color:var(--tinta-2)}
h1.titulo{font-size:1.9rem;font-weight:700;margin:0;letter-spacing:-.01em}
.subtitulo{color:var(--tinta-2);margin:.2rem 0 1.4rem;font-size:.95rem}
.envoltorio{overflow-x:auto}
.estado{display:flex;gap:2.5rem;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;
border-top:1px solid var(--costura);border-bottom:1px solid var(--costura);padding:1.1rem 0;margin-bottom:1.8rem}
.estado .frase{font-size:1.45rem;line-height:1.3;font-weight:600;max-width:46ch;text-wrap:balance}
.estado .detalle{color:var(--tinta-2);font-size:.98rem;margin-top:.5rem;max-width:62ch}
.estado .datos{font-size:.9rem;color:var(--tinta-2);min-width:19rem;line-height:1.6}
.estado .datos b{color:var(--tinta);font-weight:600}
.estado .aviso{color:var(--atencion)}
h2.seccion{font-size:1.02rem;font-weight:600;margin:0 0 .7rem;letter-spacing:.01em}
table.noche{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.93rem}
table.noche th{padding-left:.6rem;padding-right:.6rem;font-weight:500;font-size:.76rem;text-transform:uppercase;letter-spacing:.05em;color:var(--tinta-2);
text-align:left;padding-top:.4rem;padding-bottom:.4rem;border-bottom:1px solid var(--costura);white-space:nowrap}
table.noche td{white-space:nowrap;padding:.7rem .5rem;border-bottom:1px solid var(--costura);vertical-align:middle}
table.noche tr.fila:hover td{background:rgba(236,230,216,.04)}
table.noche td.parcela{white-space:normal;min-width:9.5rem}
table.noche .num{text-align:right}
table.noche .sec{color:var(--tinta-2);font-size:.82rem;display:block}
.marca-estado{display:inline-flex;align-items:center;gap:.5rem;font-weight:600;white-space:nowrap}
.marca-estado svg{flex:none}
.helada{color:var(--helada)}.atencion{color:var(--atencion)}.normal{color:var(--normal)}.sin_umbral{color:var(--neutro)}
.barra{position:relative;height:18px;min-width:170px;background:var(--pista);border-radius:2px}
.barra i{position:absolute;top:0;bottom:0;width:1px;background:var(--costura)}
.barra b{position:absolute;top:3px;bottom:3px;background:var(--helada);border-radius:1px;
transform-origin:left;animation:crece .7s var(--ease) both}
.barra b.riego{background:var(--atencion)}
.barra b.abierta{border-radius:1px 0 0 1px}
.barra em{position:absolute;top:0;bottom:0;display:flex;align-items:center;left:.5rem;font-style:normal;
font-size:.74rem;color:var(--tinta-2)}
.eje{position:relative;height:1rem;min-width:170px;font-size:.72rem;color:var(--tinta-2);font-weight:400;
text-transform:none;letter-spacing:0}
.eje span{position:absolute;transform:translateX(-50%)}
.eje span:first-child{transform:none}.eje span:last-child{transform:translateX(-100%)}
.chip.neutro{color:var(--neutro)}
table.noche tr.sin-reporte td{background:rgba(240,184,74,.07)}
.chip{display:inline-block;border:1px solid currentColor;border-radius:3px;padding:.05rem .45rem;font-size:.8rem;font-weight:600}
@keyframes crece{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@media (prefers-reduced-motion:reduce){.barra b{animation:none}}
.mapa-titulo{font-size:.86rem;color:var(--tinta-2);margin-bottom:.1rem}
.leyenda{display:flex;gap:1.2rem;flex-wrap:wrap;font-size:.8rem;color:var(--tinta-2);margin:.2rem 0 .6rem}
.punto{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--tinta);border:2px solid var(--tinta);margin-right:.4rem;box-sizing:border-box}
.punto.hueco{background:transparent;border-color:var(--atencion)}
.vacio{border:1px dashed var(--costura);border-radius:4px;padding:1.4rem;color:var(--tinta-2)}
div[data-testid="stExpander"]{border:1px solid var(--costura);border-radius:4px;background:transparent}

[data-testid="stSidebar"] [data-testid="stPageLink"]{margin:0}
[data-testid="stSidebar"] [data-testid="stPageLink"] a{min-height:0;line-height:1.3;padding:.45rem .6rem;border-radius:4px;color:var(--tinta-2);font-size:.92rem;text-decoration:none}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover{background:var(--pista);color:var(--tinta)}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"]{background:var(--pista);color:var(--tinta);font-weight:600}
[data-testid="stSidebar"] [data-testid="stPageLink"] p{font-size:.92rem;line-height:1.3;margin:0}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.15rem}
a.enlace{color:var(--tinta);text-decoration:underline;text-decoration-color:var(--costura);text-underline-offset:.2em;text-decoration-thickness:1px}
a.enlace:hover{text-decoration-color:var(--atencion);color:var(--atencion)}
.cifras{display:flex;flex-wrap:wrap;gap:.4rem 2.4rem;margin:.2rem 0 1.6rem;padding:0;font-variant-numeric:tabular-nums}
.cifras div{display:flex;flex-direction:column;gap:.1rem}
.cifras dt{font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;color:var(--tinta-2);font-weight:500}
.cifras dd{margin:0;font-size:1.05rem;font-weight:600}
.cifras dd small{font-weight:400;color:var(--tinta-2);font-size:.82rem;margin-left:.3rem}
.aviso-nodos{color:var(--atencion);font-size:.9rem;margin:.3rem 0 .8rem}
.semanas{color:var(--tinta-2);font-size:.85rem;margin-top:.7rem;line-height:1.6;font-variant-numeric:tabular-nums}
.semanas b{color:var(--tinta);font-weight:600}
table.riegos,table.q8{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.9rem}
table.riegos th,table.q8 th{font-weight:500;font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;color:var(--tinta-2);text-align:left;padding:.35rem .5rem;border-bottom:1px solid var(--costura);white-space:nowrap}
table.riegos td,table.q8 td{padding:.5rem .5rem;border-bottom:1px solid var(--costura);white-space:nowrap}
table.q8 .sec{display:block;color:var(--tinta-2);font-size:.82rem}
table.riegos .num,table.q8 .num{text-align:right}
table.riegos tr.esta-noche td,table.q8 tr.esta-noche td{background:rgba(236,230,216,.05)}
</style>
"""
