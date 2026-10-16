# ADR-009: Temperatura "sospechosa" y noche extrema

**Estado:** Aceptado (16/10/2026). Extiende la auditoría de [ADR-007](ADR-007-validacion-lecturas.md) y usa los parámetros de [ADR-005](ADR-005-parametros-simulacion.md). Campos en [`modelo-datos.md`](../modelo-datos.md), sección 3.10.

## Contexto

El campo `configuracion.sospechoso_minimo_c` se había agregado como el límite de temperatura "sospechosa" por departamento (récord de septiembre del SMN), pero **ningún componente lo usaba**: solo la documentación del simulador lo mencionaba, como techo de frío para generar las noches de helada.

Al revisarlo apareció un conflicto: el propio proyecto documenta heladas de septiembre de 2026 en el departamento de San Rafael de −7,4 a −8,3 °C (prensa, a validar), mucho más frías que el límite de −4,5 °C. Y la noche de helada precargada (RF-13) tiene que verse en el dashboard con alerta, lo que depende de la etapa de la planta ese día.

## Decisiones

**Qué es y qué hace "sospechoso"**

| # | Tema | Decisión | Descartado |
|---|---|---|---|
| 1 | Función | **Techo de generación** del simulador y **aviso de auditoría**. Una lectura sospechosa no se rechaza, no se borra ni se excluye de las consultas ni de las alertas | Eliminar el campo (dejaba el techo como constante suelta); excluir las lecturas de las consultas (cambiaría Q1, Q9 y Q10 por un dato que ya sabemos simulado) |
| 2 | Con qué se compara | Con `temperatura_c`, la lectura del sensor (abrigo), igual que el récord del SMN. Es sospechosa si es **estrictamente menor** que el límite | Compararla con la temperatura del brote (mezclaría alturas) |
| 3 | Rango del campo | Solo `maximum: 0` en el esquema. Una prueba verifica que cada límite sea más cálido que el mínimo "imposible" de `lecturas.py`, sin copiar ese valor | Rango −40 a 0 en el esquema (repite un valor provisional); sin rango |
| 4 | Un valor o uno por mes | **Un valor por departamento**: el récord de septiembre, el mes más frío de la temporada | Un valor por departamento y por mes (21 valores, uno de ellos sin fuente) |
| 5 | Tupungato | `null` (a validar). El simulador **falla con un mensaje claro** si intenta generar heladas allí sin valor, y la auditoría avisa "no auditado" sin contarlo como falla | Valor provisional de un pronóstico del INTA; copiar el de otro departamento (ambos serían inventar) |

**La noche extrema**

| # | Tema | Decisión | Descartado |
|---|---|---|---|
| 6 | Qué noches pueden superar el límite | **Una sola noche, en San Rafael**, donde el evento de 2026 está documentado | La noche precargada en las tres fincas (dos no tienen cifra); cualquier noche "severa" |
| 7 | Cómo se declara | En `configuracion.noche_extrema`: `{finca_id, inicio, fin, minimo_c}`, objeto único, con ventana explícita en UTC. El seed genera de ahí el evento climático | Declararla solo como evento climático (la auditoría se complica y no impone el alcance); no declararla (una anomalía real se confundiría con la noche extrema) |
| 8 | Cuándo | **Primera semana de octubre de 2026** (3 al 10), justo después de la brotación estimada (~1/10), cuando el umbral es −3,9 °C y la alerta se ve. El seed fija las horas y comprueba la etapa con Q9 | La fecha real del evento (7/9): según el modelo la planta está en yema dormida o hinchada y la alerta puede no verse |
| 9 | Piso | **−6,3 °C** en el sensor: la cifra de prensa (−8,3 °C) menos Δ (2 °C), **supuesto** (se presume que la prensa informó nivel del cultivo y no abrigo). A validar | Esperar la investigación con `null`; usar −8,3 °C tal cual |

**La auditoría** (`db/queries/auditoria_lecturas.py`)

| # | Tema | Decisión |
|---|---|---|
| 10 | Conteos | **Mal formadas** (no cumplen el esquema), **sospechosas esperadas** (la noche extrema: esa finca, esa ventana, sin pasar su piso) y **sospechosas inesperadas** (el resto) |
| 11 | Aprobación | Aprueba si **mal formadas = 0 e inesperadas = 0**. Las esperadas se informan aparte (cantidad y la lectura más fría). Si falla alguno de los dos ceros, el script termina con código 1 |
| 12 | Sin límite o sin configuración | Las lecturas de un departamento sin límite, o todas si falta el documento de configuración, **no se auditan como sospechosas**: se avisa de forma visible y no cuenta como falla |

## Consecuencias

- `configuracion` suma el campo obligatorio `noche_extrema` y el límite pasa a tener `maximum: 0`.
- Las reglas que el esquema no puede expresar (porque comparan dos campos) están en `configuracion.verificar_coherencia()`: cada límite más cálido que el mínimo imposible, `inicio < fin`, y piso de la noche extrema más frío que el límite de su finca. La usan las pruebas y la va a usar el seed.
- El "resultado esperado: 0" del ADR-007 pasa a ser **dos ceros**: mal formadas e inesperadas.
- La fecha exacta de la noche extrema, y la comprobación de que la parcela esté en BBCH 07 o más ese día, se resuelven al armar el seed.
- **El seed completo espera a Tupungato:** con su límite en `null` el simulador no genera heladas allí. Se desbloquea con la investigación de Tupungato (`docs/investigacion/`).
- **Pendientes a validar:** el piso de −6,3 °C (depende de si la prensa informó abrigo o nivel del cultivo), el límite de Tupungato y que las cifras de prensa del evento de 2026 sean confiables.
- Se agregó `db/departamentos.py` para traducir `"San Martín"` a la clave `san_martin`.
