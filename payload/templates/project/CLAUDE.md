# {{PROJECT_NAME}}

<!-- Project-specific instructions only. Global engineering standards are
     inherited automatically from ~/.claude/CLAUDE.md; do not copy them here. -->

## What this project is
{{ONE_LINE_DESCRIPTION}}

## Commands
- Install: `TODO`
- Test: `TODO`
- Lint/typecheck: `TODO`
- Run: `TODO`

## Project rules
- TODO: architecture constraints, conventions, forbidden changes.

## Git policy
- Commits: only when asked.
- Push: only when asked.
<!-- To enable auto-push at task closure, replace the line above with:
     Auto-push: at task closure (validated, reviewed if required, scoped commit)
     push the current branch to its upstream and verify sync. -->

## Session state
This project uses the Starter Kit session convention (opt-in): durable handoff lives in `.ai/STATE.md` (send `START` to resume, `END` to close). Remove `.ai/STATE.md` and this section to opt out; your own start/end workflow always takes precedence.
