# Flujo de trabajo en Git

Proyecto de grupo de dos integrantes, con Federico Barboza como autor. Repositorio público.

## Ramas

- `main`: siempre estable y demostrable.
- Ramas de trabajo con prefijo: `docs/...`, `feat/...`, `perf/...`, `chore/...`, `fix/...`. Ejemplo: `feat/simulador-base`.
- Ramas cortas: se integran en uno o dos días.

## Commits

Formato Conventional Commits, en español:

```
tipo(ámbito): descripción corta (#issue)
```

| Tipo | Uso |
|---|---|
| `feat` | Colecciones, consultas, simulador, dashboard |
| `docs` | Documentación |
| `perf` | Índices y optimizaciones |
| `chore` | Estructura, scripts, configuración |
| `fix` | Corrección de errores |

Ejemplo: `docs(requisitos): agrega consultas principales (#3)`.

## Ciclo de cada tarea

1. Crear o tomar un **issue** (máximo 3 a 4 horas; si es más grande, dividirlo).
2. Crear la **rama** desde `main` actualizado.
3. Hacer commits pequeños.
4. Abrir un **pull request** con `Closes #N`.
5. **Revisión:** el autor repasa el cambio con la lista del pull request; si el otro integrante del grupo participa, también lo revisa.
6. Merge a `main` y borrar la rama.

```bash
git switch main && git pull
git switch -c feat/simulador-base
# ...trabajo...
git add simulator/
git commit -m "feat(simulador): genera lecturas de la temporada (#8)"
git push -u origin feat/simulador-base
```

## Reglas

- Nadie hace merge de un pull request sin repasar antes la lista de verificación.
- No se reescribe la historia de `main` ni se usa `push --force` sobre ramas compartidas.
- Los conflictos se resuelven hablando, no sobrescribiendo.
- Cada persona trabaja con su propia cuenta de GitHub, para que el aporte individual quede registrado.

## Issues, milestones y labels

- Un **milestone** por sprint (A, B, C y Cierre).
- Labels: `feature`, `bug`, `spike`, `docs`, `perf`, `chore`, y por área: `db`, `dashboard`, `simulador`.
- Cada issue tiene responsable asignado.

## Seguridad (repo público)

Nunca subir credenciales, cadenas de conexión con contraseña, backups ni archivos `.env`. Revisar `.gitignore` antes del primer commit y la lista de verificación del pull request antes de cada merge.

## Versiones

Etiqueta `v1.0.0` al cierre, sobre `main` congelado.
