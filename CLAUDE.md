# cs-topics — AI Agent Instructions

## Domain / Scientific Context

<!-- The real-world problem this project addresses. State the claim/objective, the outcome,
     and — critically — the data provenance (own data? regional/Peruvian domain? public source?).
     This is the differentiator; be concrete. -->

- **Problem**: <!-- fill -->
- **Outcome / target**: <!-- fill -->
- **Data provenance**: <!-- fill: source, ownership, how acquired -->

## Architecture

<!-- How the project runs. If it's a pipeline, describe the stages and the data flow between them. -->

```bash
# e.g. uv run ingest && uv run features && uv run model
```

## Key Files

| File | Purpose |
|------|---------|
| `src/cs_topics/...` | <!-- fill --> |
| `configs/...` | <!-- fill --> |

## Data Conventions

<!-- Adjust/remove if this is not a data project. Defaults reflect the medallion + polars/duckdb stack. -->

- **Layers**: raw → `data/bronze/`, cleaned → `data/silver/`, analytic → `data/gold/`. All gitignored.
- **Polars over pandas** everywhere; only drop to numpy when a library requires it.
- **DuckDB for SQL joins** across parquet; Polars for local transforms.
- **Remote silver**: reference the remote root via `$SILVER` in SQL when pulling shared data.
- Keep dates as typed `Date`, never strings, in intermediate tables.

## Conventions

<!-- Project-specific rules: ID normalization, seeds, temporal discipline, naming, etc. -->


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
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
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
