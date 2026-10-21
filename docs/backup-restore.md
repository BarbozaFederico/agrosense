# Backup y restauración

**Estado:** backup y restauración listos y probados (21/10/2026). Decisiones en [ADR-016](decisions/ADR-016-backup-y-restauracion.md). Requisitos RNF-02 y RNF-03. Los usuarios y roles (RNF-04) se agregan en el cambio siguiente.

## En tres comandos

```bash
python -m scripts.backup_restore.backup                                              # hace el backup y borra las copias que sobran
python -m scripts.backup_restore.restaurar --comparar-con agrosense                  # restaura el último en agrosense_restaurada y lo verifica
python -m scripts.backup_restore.probar_respaldo                                     # 19 casos automáticos (usa agrosense_tests)
```

Requisito: MongoDB Database Tools (`winget install MongoDB.DatabaseTools`). El instalador no los agrega al PATH; los scripts los encuentran solos en `C:\Program Files\MongoDB\Tools\*\bin`, o en la carpeta de la variable `AGROSENSE_HERRAMIENTAS`.

## Política

Estos números no tienen fuente: son un **supuesto adoptado** por el equipo (ADR-012 y ADR-016).

| Tema | Política |
|---|---|
| Frecuencia | Un backup por día a las 02:00 |
| Retención | La última copia de cada uno de los **7 días** más recientes y la de los **4 últimos domingos** (unas 10 copias a la vez). El resto se borra |
| Qué se respalda | La base `agrosense` completa, en un solo archivo `.archive.gz`. Los usuarios no se incluyen |
| Dónde | Fuera del repositorio, que es público: `~/agrosense-backups` o la carpeta de `AGROSENSE_BACKUP_DIR`. El script se niega a guardar dentro del repo |
| Pérdida máxima | Lo ocurrido desde el último backup (24 h). La instancia es una sola, sin réplicas ni oplog: no hay recuperación a un instante |
| Tamaño | 2,4 MB por copia (727.980 lecturas comprimidas) |

La retención se decide en `seleccionar_a_borrar` (`scripts/backup_restore/backup.py`). Si hay dos copias el mismo día queda la más nueva; un domingo cuenta como diario mientras esté entre los 7 días más recientes y, después, como semanal hasta completar 4.

## Procedimiento

### Hacer un backup

```bash
python -m scripts.backup_restore.backup                      # base "agrosense" (o la de AGROSENSE_BD)
python -m scripts.backup_restore.backup --destino D:/respaldos --sin-rotar
```

Genera dos archivos: `agrosense_AAAAMMDD_HHMMSS.archive.gz` (el volcado, hecho con `mongodump --db agrosense --archive --gzip`) y `agrosense_AAAAMMDD_HHMMSS.manifiesto.json` con la huella `sha256`, el tamaño, la versión del servidor y, por colección, tipo, documentos, nombres de índices y huella del validador. El manifiesto no tiene datos ni credenciales.

### Restaurar

```bash
python -m scripts.backup_restore.restaurar                                   # el último backup, en agrosense_restaurada
python -m scripts.backup_restore.restaurar RUTA.archive.gz --destino prueba  # un archivo concreto, en otra base
python -m scripts.backup_restore.restaurar --comparar-con agrosense          # y además corre Q1, Q5, Q9 y Q10 en las dos bases
```

1. Comprueba que el archivo no cambió (huella `sha256`). Si cambió, **no restaura nada**.
2. Se niega a escribir en una base que ya existe. Para sobrescribirla hay que pedirlo con `--reemplazar`.
3. Ejecuta `mongorestore` con `--nsFrom` y `--nsTo` (`agrosense.*` → `agrosense_restaurada.*`).
4. Compara la base restaurada con el manifiesto y, si se pide, con la base original. Termina con código 1 si algo difiere.

### Si se pierde la base (desastre)

```bash
python -m scripts.backup_restore.restaurar --reemplazar                      # vuelve a dejar "agrosense" como estaba en el último backup
```

`--reemplazar` borra cada colección antes de restaurarla (`mongorestore --drop`). Se usa a propósito: sin ese permiso explícito, el script nunca toca una base que existe.

### Programarlo (no registrado)

Ejemplo para el Programador de tareas de Windows. **No se registró ninguna tarea** en este equipo (ADR-016) y el comando no se probó acá; se deja para quien lo necesite:

```bash
schtasks /Create /SC DAILY /ST 02:00 /TN "agrosense-backup" /TR "cmd /c cd /d C:\ruta\agrosense && .venv\Scripts\python.exe -m scripts.backup_restore.backup" /F
```

Si la notebook está apagada a las 02:00, la tarea no corre salvo que se active "ejecutar lo antes posible si se perdió el inicio programado". La rotación va incluida en el mismo script.

## Cómo funciona

- **La serie temporal.** MongoDB guarda las lecturas agrupadas en *buckets*. `mongodump` copia esos buckets (2.529 documentos para las 727.980 lecturas) y `mongorestore` reconstruye la colección como serie temporal. Se comprobó que vuelve con el mismo tipo, las mismas lecturas y los mismos índices.
- **Los índices y los validadores** viajan dentro del archivo: después de restaurar no hay que volver a crearlos.
- **El manifiesto** permite verificar una restauración aunque la base original ya no exista (en un desastre real, justamente).
- **Ubicación segura.** `directorio_de_respaldos` rechaza cualquier carpeta dentro del repositorio (RNF-07). `.gitignore` además excluye `backups/`, `dump/`, `*.archive` y `*.gz`.

## Prueba de restauración (RNF-03)

**Fecha:** 21/10/2026. **Servidor:** MongoDB 9.0.2. **Herramientas:** Database Tools 100.19.1. **Base:** `agrosense` real.

```text
$ python -m scripts.backup_restore.backup
Backup de agrosense: C:\Users\g3d3g\agrosense-backups\agrosense_20261021_120816.archive.gz
  2445 KB, sha256 85c204749f28adcc…, MongoDB 9.0.2
  lecturas                      727980 documentos  timeseries
  riegos 563 · alertas 35 · observaciones_fenologicas 42 · nodos 12 · parcelas 6 · fincas 3 · variedades 1 · configuracion 1 · eventos_climaticos 1
Rotación: 0 copia(s) borrada(s) (7 diarios + 4 semanales)

$ python -m scripts.backup_restore.restaurar --comparar-con agrosense
Restaurando agrosense_20261021_120816.archive.gz en la base agrosense_restaurada…
  lecturas                      727980 documentos  timeseries  2 índices
  (las otras 9 colecciones, con los mismos conteos y sus índices)
  Q1: igual en las dos bases
  Q5: igual en las dos bases
  Q9: igual en las dos bases
  Q10: igual en las dos bases
RESULTADO: la base restaurada coincide con el manifiesto y con agrosense en Q1, Q5, Q9, Q10
```

(Salida abreviada: se omiten las líneas de las colecciones chicas.) Qué se comprobó: las 10 colecciones con el mismo número de documentos, `lecturas` otra vez como serie temporal, los índices (incluidos los `2dsphere` y el automático de la serie temporal), los validadores, y que Q1, Q5, Q9 y Q10 devuelven exactamente el mismo resultado en la base original y en la restaurada. La base `agrosense_restaurada` queda creada para inspeccionarla en Compass; se borra con `db.dropDatabase()` desde `mongosh`.

### Pruebas automáticas

`python -m scripts.backup_restore.probar_respaldo` (19 casos, sobre `agrosense_tests` y una carpeta temporal):

| Grupo | Qué comprueba |
|---|---|
| Rotación | Con 52 copias inventadas (1/9 al 21/10) se conservan 10: los días 15 a 21/10 y los domingos 11/10, 4/10 y 27/9; entre dos copias del mismo día queda la más nueva; con pocas copias no se borra nada. Resultados esperados escritos a mano |
| Ubicación y herramientas | Se niega a guardar dentro del repo; encuentra `mongodump` y `mongorestore` |
| Backup real | Archivo y manifiesto; el manifiesto coincide con la base (10 colecciones, 727.980 lecturas en una serie temporal); la huella coincide |
| Restauración | Coincide con el manifiesto; `lecturas` vuelve como serie temporal; vuelven los 7 índices del proyecto y el automático; Q1, Q5, Q9 y Q10 iguales |
| Protecciones | No pisa una base existente ni la original sin `--reemplazar` (y sus datos siguen intactos); un archivo con un byte cambiado se detecta y no se restaura nada |
| Desastre | Se borra `riegos` y se vacía `alertas` en la copia, la comparación lo detecta, y con `--reemplazar` vuelven 563 riegos y 35 alertas |
| Rotación real | De 10 archivos reales se borran los 3 más viejos con sus manifiestos |

## Límites conocidos

- **Pérdida de hasta 24 h** de lecturas entre dos backups (instancia sola, sin oplog).
- **No es una foto instantánea:** si alguien escribe mientras corre `mongodump`, el respaldo puede mezclar momentos. En este proyecto se escribe al cargar datos, no durante el backup.
- **Los usuarios no se respaldan.** Se recrean con el script de roles (próximo cambio, ADR-017), así los hashes de contraseñas nunca quedan en un respaldo.
- **Los scripts se conectan hoy sin credenciales** (`AGROSENSE_URI`). Al activar la autenticación habrá que usar el usuario `respaldo` sin que su clave aparezca en la línea de comandos.

## Usuarios y roles

*A completar en el cambio siguiente (ADR-017, RNF-04):* cuatro usuarios (`admin`, `dashboard`, `simulador` y `respaldo`) con autenticación activada, sus permisos y la prueba de que cada uno solo puede lo que le corresponde.
