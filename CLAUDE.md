# cs-topics — AI Agent Instructions

Repo del curso **Tópicos en Ciencias de la Computación (1ACC0058)**, UPC, ciclo 2026-20.
No es un proyecto de software con usuarios: es el cuaderno de trabajo de un ciclo.

## Contexto

- **Qué es**: apuntes por sesión + material oficial del Aula Virtual + código de los TPs.
- **Temario**: research en CS (U1), Constraint Programming (U2-U4), agentes/MDP/FIPA con JADE (U5), outcome ABET (U6).
- **Procedencia del material**: Aula Virtual UPC (curso `_546154_1`). `manifest.json` es la
  fuente canónica: qué documentos existen, qué adjuntos se esperan y de qué URL salen.
  Es material del profesor y **este repo es público**, así que `materials/` NO se versiona:
  vive solo en local y se reconstruye entero con `aula sync` a partir del manifiesto
  (ver `~/Code/personal/chrome-helper`). La única excepción es
  `materials/AULA-VIRTUAL-ESTADO.md`, que es resumen propio, no material ajeno.
- **Sílabo**: aún NO publicado al 2026-08-28. La numeración de unidades puede cambiar;
  no la trates como estable.

## Arquitectura

Estructura por tipo, no por semana — las unidades pueden reordenarse, los labs no.

```bash
notes/         # apuntes .md por sesión (_template.md es la plantilla)
materials/     # PDFs y slides del profe, carpeta por semana (week-NN/)
labs/cp/       # Constraint Programming — Python + OR-Tools, gestionado con uv
labs/agents/   # JADE / FIPA — Java 21 + javac + Makefile, sin Maven ni Gradle
```

Cada lab es una raíz de proyecto independiente con su propio toolchain:

```bash
cd labs/cp     && uv sync && uv run pytest
cd labs/agents && make deps && make run AGENT=upc.topicos.week11.HolaAgent
```

## Archivos clave

| Archivo | Propósito |
|------|---------|
| `manifest.json` | Inventario canónico del Aula Virtual. Fuente de verdad para saber qué material falta. |
| `materials/AULA-VIRTUAL-ESTADO.md` | Estado del curso al momento del volcado (sílabo, notas, fechas). |
| `notes/_template.md` | Plantilla de apunte de sesión. |
| `labs/cp/models/nqueens.py` | Ejemplo de referencia CP-SAT: modelo → restricciones → solver. |
| `labs/agents/fetch-deps.sh` | Baja `jade.jar` de Maven Central (`net.sf.ingenias:jade:4.3`). |
| `labs/agents/Makefile` | Compila y arranca la plataforma JADE. |

## Convenciones

- **Apuntes en español**, nombrados `week-NN-<tema-en-kebab>.md`. Copia `_template.md`.
- **Material NO versionado**: `materials/` está en `.gitignore` (repo público, material
  del profesor). Se reconstruye con `aula sync`; `manifest.json` es la receta y sí se
  commitea. Los jars de `labs/agents/lib/` tampoco — se bajan con `make deps`.
- **Ramas**: `main` estable, `dev` de integración, `feat/<algo>` para cada trabajo.
  Nada va directo a `main`.
- **Los labs se escriben con TDD**: test primero, luego el modelo o el agente.
- La plataforma JADE no termina sola; `make run` se corta con Ctrl-C. No la lances
  en foreground esperando que retorne.
- Python 3.14 del sistema NO sirve para OR-Tools; `labs/cp` fija `<3.14` y `uv`
  se encarga de bajar un intérprete compatible.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:970c3bf2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   bd dolt push
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
