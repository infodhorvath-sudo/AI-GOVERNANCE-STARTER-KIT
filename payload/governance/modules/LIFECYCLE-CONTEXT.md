# LIFECYCLE & CONTEXT MODULE

On-demand module of the Global AI Governance (see `GLOBAL-RULES.md`). Read when
the user says START or END, asks for a handoff, or a context reset is near.

# 1. WHEN THIS CONVENTION APPLIES

Opt-in. It applies only in a project that has `.ai/STATE.md` (bootstrapped by
the kit or adopted by the team). Elsewhere `start` and `end` are ordinary words:
do not create `.ai/` files because the user typed them, do not duplicate or
replace a workflow the user already has (their own `start`/`end` skills or
commands, `QUEUE.md`/`HANDOFF.md`, ...), and ask once if it is unclear which
workflow is meant.

In an adopted project, the standalone commands (case-insensitive) are `START` /
`start session` and `END` / `finish session`; the same words inside ordinary
sentences are not triggers. The optional hook (`install.py --hooks`) injects a
reminder only when the prompt is exactly one of these commands **and** the
current project has `.ai/STATE.md`.

# 2. START SESSION

1. Load global and project governance (project `CLAUDE.md`).
2. Read `.ai/STATE.md` and the latest `.ai/SESSION-LOG.md` entry, if present.
3. Inspect actual Git state: branch, HEAD, upstream, dirty files. Derive these
   at runtime; never trust a stored "current HEAD".
4. Compare recorded state with the repository; reconcile safe discrepancies.
5. Determine the Exact Next Action.
6. If state is coherent, an Exact Next Action is recorded and nothing blocks
   (no safety gate, missing information or conflicting priority), start it
   without asking permission.
7. If the project has no `.ai/` state it has not adopted this convention: say so,
   do not invent state, and offer `bootstrap-project.py` only if the user wants it.

# 3. END SESSION

1. Finish already-implied safe work; run relevant validation.
2. Update `.ai/STATE.md` (replace; current logical state + Exact Next Action).
3. Append an entry to `.ai/SESSION-LOG.md` (what was done, evidence, open items).
4. Commit/push only as the project policy allows (see AUTONOMY-GIT-SAFETY §3).
5. Verify final Git state.
6. Close with a short reminder: open a fresh conversation (in Claude Code:
   `/clear` or a new chat) and send `START`.

# 4. DURABLE ARTIFACTS

- `.ai/STATE.md` — canonical handoff: current state, Exact Next Action,
  blockers, decisions that must survive. Replaced, not appended.
- `.ai/SESSION-LOG.md` — append-only history; not current-state authority.
- Never store runtime Git facts (current HEAD) in tracked state; a clearly
  labelled historical checkpoint SHA is fine.
- Do not create duplicate current-state files (e.g. NEXT-SESSION.md).

# 5. CONTEXT HYGIENE

At a natural boundary (a substantial self-contained milestone, not every small
action) persist state so the user may optionally start a fresh conversation and
send `START`. Say it is safe to clear only when STATE.md is current with an
Exact Next Action, validation passed, Git state is understood and no decision
lives only in chat. Never perform the reset yourself.
