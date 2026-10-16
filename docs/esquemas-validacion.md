# Esquemas de validación (`$jsonSchema`)

**Fecha:** 16/10/2026 · **Versión probada:** MongoDB Server 9.0.2, Python 3.13, `pymongo` 4.18.3 · **ADR:** [ADR-006](decisions/ADR-006-modelo-de-datos.md), [ADR-007](decisions/ADR-007-validacion-lecturas.md) y [ADR-008](decisions/ADR-008-esquemas-en-python.md) y [ADR-009](decisions/ADR-009-temperatura-sospechosa-y-noche-extrema.md) · **Modelo:** [`modelo-datos.md`](modelo-datos.md)

## Qué resuelve

Un `$jsonSchema` es una regla que describe cómo tiene que ser un documento: qué campos tiene, de qué tipo y con qué valores. MongoDB la usa para **rechazar** los documentos que no la cumplen. Así la base nunca guarda datos mal formados, aunque el simulador o una persona se equivoquen.

Los esquemas están escritos en **Python** (ADR-008), pero la regla la guarda y la aplica **el servidor de MongoDB**: Python solo la envía.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| [`db/conexion.py`](../db/conexion.py) | Conexión a MongoDB, configurable con las variables `AGROSENSE_URI` y `AGROSENSE_BD` |
| [`db/schemas/comunes.py`](../db/schemas/comunes.py) | Piezas que se repiten: número, porcentaje, fecha, punto y polígono GeoJSON, códigos legibles (`F-SR`, `P-SR-1`, `N-SR-1-A`) y etapa BBCH |
| `db/schemas/fincas.py`, `parcelas.py`, `nodos.py`, `lecturas.py`, `alertas.py`, `riegos.py`, `eventos_climaticos.py`, `observaciones_fenologicas.py`, `variedades.py`, `configuracion.py` | Un esquema por colección, con comentarios que explican cada regla |
| [`db/schemas/__init__.py`](../db/schemas/__init__.py) | Lista de los 10 esquemas, en el orden en que se crean |
| [`db/schemas/crear.py`](../db/schemas/crear.py) | Crea las colecciones, instala los validadores y comprueba que quedaron bien |
| [`db/schemas/validar.py`](../db/schemas/validar.py) | Valida documentos **sin guardarlos**: lo usa el simulador con las lecturas (ADR-007) |
| [`db/schemas/crear_colecciones.py`](../db/schemas/crear_colecciones.py) | Script para crear las colecciones en la base real (`agrosense`) |
| [`db/schemas/probar_esquemas.py`](../db/schemas/probar_esquemas.py) | Prueba de los 10 esquemas en la base de prueba (`agrosense_tests`) |
| [`db/queries/auditoria_lecturas.py`](../db/queries/auditoria_lecturas.py) | Cuenta las lecturas mal formadas y las "sospechosas" (esperadas e inesperadas), y termina con error si falla alguno de los dos ceros (ADR-007 y ADR-009) |
| [`db/departamentos.py`](../db/departamentos.py) | Traduce `"San Martín"` a la clave `san_martin` que usa `configuracion` |

## Cómo se usa

Todos los comandos se corren **desde la raíz del repositorio** y con el entorno virtual activado (`source .venv/Scripts/activate` en Git Bash). Se usa `python -m` para que funcionen los `import` del paquete `db`.

Crear las colecciones en la base real:

```bash
python -m db.schemas.crear_colecciones
```

Se puede correr más de una vez: si una colección ya existe, actualiza su validador y **no borra datos**. Para usar otra base, en Git Bash:

```bash
AGROSENSE_BD=agrosense_tests python -m db.schemas.crear_colecciones
```

Probar los esquemas (borra y recrea `agrosense_tests`):

```bash
python -m db.schemas.probar_esquemas
```

Auditar `lecturas` después de cada carga (resultado esperado: 0 mal formadas):

```bash
python -m db.queries.auditoria_lecturas
```

Validar lecturas desde el simulador, antes de insertarlas:

```python
from db.schemas import lecturas
from db.schemas.validar import validar_documentos

validos, invalidos = validar_documentos(bd, lecturas.ESQUEMA, lote)
bd.lecturas.insert_many(validos)
```

## Reglas de los esquemas

**Para todas las colecciones comunes** (ADR-006):

- `validationLevel: "strict"`: se valida cada insert y cada update.
- `validationAction: "error"`: el documento inválido se rechaza.
- Esquema cerrado (`additionalProperties: False`): un campo que no está en el esquema, por ejemplo un error de tipeo, hace que se rechace el documento. Vale también para los subdocumentos.
- `_id` declarado en el esquema; si no, el esquema cerrado rechaza todo (spike de esquemas, prueba 1).

**`lecturas` es la excepción** (ADR-007): como serie temporal no admite validador. Su esquema se usa de dos formas: el simulador valida cada lote antes de insertarlo (`validar.py`) y la auditoría busca después las que no lo cumplen. En este esquema `_id` no es obligatorio, porque las lecturas se validan antes de tenerlo.

**Reglas que combinan campos.** Algunas reglas dependen de dos campos a la vez. Se escriben con `allOf` (tiene que cumplir todas) y `anyOf` (tiene que cumplir al menos una):

| Colección | Regla |
|---|---|
| `alertas` | Abierta ⇒ `fin` es `None`; cerrada ⇒ `fin` es una fecha |
| `alertas` | El `riesgo` solo existe en alertas de helada cerradas; en el resto es `None` |
| `riegos` | Si el `origen` es `"alerta"`, `alerta_id` es obligatorio |

**Otros controles destacados:**

| Colección | Control |
|---|---|
| `fincas`, `parcelas`, `nodos` | El `_id` tiene que respetar el formato (`pattern`): `F-SR`, `P-SR-1`, `N-SR-1-A` |
| `parcelas`, `riegos` | Superficie, lámina y litros mayores que 0 (`exclusiveMinimum`) |
| `nodos` | La lista de variables no puede repetir elementos (`uniqueItems`) |
| `lecturas` | Temperatura entre −40 y 60 °C, humedades entre 0 y 100 %: descarta valores imposibles |
| `observaciones_fenologicas` | `observador` solo acepta un rol (`"tecnico"`, `"encargado"`), nunca un nombre |
| `configuracion` | Un solo documento, con `_id: "general"` |
| `configuracion` | `sospechoso_minimo_c`: cada límite es un número ≤ 0 o `None` (Tupungato, a validar); no admite claves con tilde ni de más |
| `configuracion` | `noche_extrema`: `{finca_id, inicio, fin, minimo_c}`, todos obligatorios, fechas de tipo fecha y `minimo_c` ≤ 0 |

## Reglas que el esquema no puede expresar

Algunas reglas comparan dos campos y un `$jsonSchema` no puede escribirlas. Están en `configuracion.verificar_coherencia()` (la usan las pruebas y la va a usar el seed):

| Regla |
|---|
| Cada `sospechoso_minimo_c` es más cálido que el mínimo "imposible" de `lecturas.py` (hoy −40, provisional) |
| `noche_extrema.inicio` es anterior a `noche_extrema.fin` |
| La finca de la noche extrema existe, su departamento tiene límite y `minimo_c` es más frío que ese límite |

## Auditoría de lecturas sospechosas (ADR-009)

`python -m db.queries.auditoria_lecturas` informa tres conteos:

| Conteo | Qué es | Esperado |
|---|---|---|
| Mal formadas | No cumplen el esquema de `lecturas` | 0 |
| Sospechosas esperadas | Más frías que el límite de su departamento, pero dentro de la noche extrema (esa finca, esa ventana) y sin pasar su piso | Se informan aparte, con la lectura más fría |
| Sospechosas inesperadas | El resto de las lecturas más frías que el límite, incluidas las que pasan el piso de la noche extrema o caen en otra finca | 0 |

Aprueba si mal formadas = 0 e inesperadas = 0; si no, termina con código 1. Las lecturas de un departamento sin límite (Tupungato) y todas, si falta el documento de configuración, **no se auditan como sospechosas**: se avisa y no cuenta como falla.

## Cómo se probó

`probar_esquemas.py` crea las 10 colecciones en `agrosense_tests` e intenta insertar, en cada colección común, un documento válido (tiene que entrar) y varios inválidos (tienen que rechazarse). Para `lecturas` prueba las dos protecciones del ADR-007 con 1 lectura válida y 3 inválidas:

1. `validar_documentos` tiene que separar 1 válida y 3 inválidas, **sin guardar nada**.
2. Insertando las 4 sin validar (como si alguien saltara el simulador), la auditoría tiene que encontrar las 3 mal formadas.

## Resultados

**Creación:** las 10 colecciones se crearon bien. Las 9 comunes quedaron con validador; `lecturas` quedó como serie temporal sin validador.

| Colección | Caso | Esperado | Resultado |
|---|---|---|---|
| `fincas` | Válido | Entra | ✔ |
| `fincas` | `_id` con formato incorrecto (`"finca1"`) | Rechazo | ✔ |
| `fincas` | Departamento fuera de la lista | Rechazo | ✔ |
| `fincas` | Campo de más (`propietario`) | Rechazo | ✔ |
| `parcelas` | Válido | Entra | ✔ |
| `parcelas` | Superficie 0 | Rechazo | ✔ |
| `parcelas` | Geometría que no es polígono | Rechazo | ✔ |
| `nodos` | Válido | Entra | ✔ |
| `nodos` | Estado fuera de la lista (`"reportando"`) | Rechazo | ✔ |
| `nodos` | Variable repetida | Rechazo | ✔ |
| `alertas` | Helada cerrada con riesgo | Entra | ✔ |
| `alertas` | Abierta, con `fin` y `riesgo` en `None` | Entra | ✔ |
| `alertas` | Abierta pero con fecha de fin | Rechazo | ✔ |
| `alertas` | Cerrada sin fecha de fin | Rechazo | ✔ |
| `alertas` | Alerta de riego con riesgo | Rechazo | ✔ |
| `alertas` | Nivel de riesgo fuera de la lista | Rechazo | ✔ |
| `riegos` | Riego por turno | Entra | ✔ |
| `riegos` | Riego por alerta con `alerta_id` | Entra | ✔ |
| `riegos` | Riego por alerta sin `alerta_id` | Rechazo | ✔ |
| `riegos` | Litros negativos | Rechazo | ✔ |
| `riegos` | Falta `lamina_mm` | Rechazo | ✔ |
| `eventos_climaticos` | Válido | Entra | ✔ |
| `eventos_climaticos` | Tipo fuera de la lista (`"tornado"`) | Rechazo | ✔ |
| `observaciones_fenologicas` | Válido | Entra | ✔ |
| `observaciones_fenologicas` | Etapa BBCH 120 (fuera de rango) | Rechazo | ✔ |
| `observaciones_fenologicas` | Observador con nombre de persona | Rechazo | ✔ |
| `variedades` | Válido | Entra | ✔ |
| `variedades` | Etapa con un campo de más | Rechazo | ✔ |
| `variedades` | Mes de inicio 13 | Rechazo | ✔ |
| `configuracion` | Válido | Entra | ✔ |
| `configuracion` | `_id` distinto de `"general"` | Rechazo | ✔ |
| `configuracion` | Porcentaje mayor que 100 | Rechazo | ✔ |
| `lecturas` | `validar_documentos` con 4 lecturas | 1 válida y 3 inválidas | ✔ |
| `lecturas` | La validación no guardó nada | 0 documentos | ✔ |
| `lecturas` | Auditoría después de insertar las 4 sin validar | 3 mal formadas | ✔ |

**Casos nuevos de `configuracion` (ADR-009):**

| Caso | Esperado | Resultado |
|---|---|---|
| Límite de frío positivo | Rechazo | ✔ |
| Falta `noche_extrema` | Rechazo | ✔ |
| `noche_extrema` con `minimo_c` positivo | Rechazo | ✔ |
| `noche_extrema` con `finca_id` de formato incorrecto | Rechazo | ✔ |
| `noche_extrema` con la fecha de inicio como texto | Rechazo | ✔ |
| `noche_extrema` con un campo de más | Rechazo | ✔ |
| Tupungato con un valor numérico en vez de `None` | Válido | ✔ |

**Reglas de coherencia (6 casos):** configuración coherente (sin errores); límite más frío que lo imposible; ventana con inicio posterior al fin; piso de la noche extrema más cálido que el límite; noche extrema en Tupungato (sin límite); noche extrema en una finca que no existe. Todos dieron el error esperado, y uno solo cada vez.

**Auditoría de sospechosas (10 casos):** con 10 lecturas de prueba (incluida una exactamente en el límite, que **no** es sospechosa):

| Chequeo | Esperado | Resultado |
|---|---|---|
| Mal formadas | 0 | ✔ |
| Esperadas y la más fría | 3 y −6,3 °C | ✔ |
| Inesperadas (fuera de la noche, bajo el piso, otra finca) | 3 | ✔ |
| Fincas sin límite, no auditadas | `F-TU` | ✔ |
| Con inesperadas no aprueba; como script termina con código 1 | Falla | ✔ |
| Sin inesperadas aprueba; como script termina con código 0 | Aprueba | ✔ |
| Sin documento de configuración: avisa y audita solo el formato | Aviso | ✔ |

**Resultado: los 62 casos dieron lo esperado.**

**Segunda corrida de `crear_colecciones.py`** sobre la misma base, que ya tenía colecciones y datos: las 9 comunes se actualizaron con `collMod`, `lecturas` se reconoció como serie temporal existente y los documentos se conservaron.

**Auditoría como script:** `auditoria_lecturas.py` informó las lecturas totales, los tres conteos y los avisos, y su código de salida coincidió con el resultado.

## Conclusiones

1. **Las 9 colecciones comunes quedan protegidas por la base:** aceptan los documentos válidos y rechazan campos de más, errores de tipeo, tipos y valores fuera de la lista, rangos imposibles, formatos de código incorrectos y combinaciones inconsistentes (por ejemplo, una alerta abierta con fecha de fin).
2. **`lecturas` queda protegida en dos niveles,** con el mismo esquema: el simulador valida antes de insertar (MongoDB valida sin guardar) y la auditoría controla después (ADR-007).
3. **Hay un solo esquema por colección,** en Python, que usan la creación de la base, el simulador y la auditoría (ADR-008).
4. **La base se puede reconstruir desde el repositorio** con un solo comando (RNF-05), y el script se puede repetir sin perder datos.
5. **Para la defensa:** `probar_esquemas.py` muestra en vivo, caso por caso, cómo MongoDB rechaza los datos mal formados.

## Pendiente

- Usar `validar_documentos` en el simulador cuando se escriba.
- Índices (`db/indexes/`), que van en una tarea aparte.
- Validar `configuracion.sospechoso_minimo_c.tupungato` (hoy `None`): Tupungato no tiene estación del SMN. Bloquea el seed completo (ADR-009).
- Validar el piso de la noche extrema (−6,3 °C, supuesto): depende de si la prensa informó temperatura de abrigo o de nivel del cultivo.
- Fijar las horas exactas de la noche extrema al armar el seed, comprobando con Q9 que la parcela de San Rafael esté en BBCH 07 o más.
