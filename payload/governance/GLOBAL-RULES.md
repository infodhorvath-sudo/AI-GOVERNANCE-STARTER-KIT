# GLOBAL AI GOVERNANCE (Starter Kit)

Kit-Version: 1.0.1
Governance-Canary: AIGOV-KIT-1.0.1-LOADED (harmless marker: if the user asks for the
governance canary, answer with exactly this value)

Compact, always-loaded core of portable working rules for AI-assisted
software work with Claude Code. Applies to every project unless that project's
own `CLAUDE.md` says otherwise. Objective: useful autonomy, few interruptions,
reproducibility, controlled cost, safety on genuinely risky actions, durable
continuity between sessions.

---

# 1. AUTHORITY

Order of authority:

1. The user's explicit current instruction (platform safety rules still apply).
2. Project governance: the project's `CLAUDE.md`, rules and canonical decisions.
3. These global rules.
4. Skills, plugins and tool defaults.

Global rules say HOW to work; the project says WHAT is true for it. Do not
reinterpret project rules with generic conventions, and do not reopen settled
project decisions unless the user asks or new evidence shows a real conflict.
Read project governance before material implementation.

---

# 2. MODULES (load on demand)

Detailed procedures live in `~/.claude/ai-governance/modules/`. Do NOT preload
them. Read one only when the task enters its scope; ordinary low-risk work
needs none.

- START / END a session, handoff, context reset, checkpoint:
  `~/.claude/ai-governance/modules/LIFECYCLE-CONTEXT.md`
- commit, push, merge, deploy, destructive or safety-sensitive action,
  unexpected repository state:
  `~/.claude/ai-governance/modules/AUTONOMY-GIT-SAFETY.md`
- model/effort choice, review, skills/plugins, subagents, agent topology:
  `~/.claude/ai-governance/modules/COST-REVIEW-TOOLS.md`

**Default coding standard: Ponytail.** For software engineering work
(features, fixes, refactors, scripts, tests, infrastructure):

1. Check whether the functionality already exists.
2. Prefer reusing existing implementations.
3. Choose the smallest correct solution.
4. Avoid needless abstractions, dependencies, services and speculative features.
5. Preserve existing architecture and project conventions.
6. Implement only what the task needs.
7. Keep appropriate tests, error handling, safety and data integrity.

If the `ponytail` skill is installed (`~/.claude/skills/ponytail`), it holds the
detail. Ponytail never overrides user instructions, project requirements,
security boundaries or required tests; it removes needless complexity, not
safeguards.

---

# 3. AUTONOMY

Once objective and scope are clear, do routine, reversible, local work without
asking: inspect, edit scoped files, run builds/tests/lint, fix errors.
Do not ask "should I proceed?" when the next safe action is obvious.

Git actions are governed by `AUTONOMY-GIT-SAFETY.md` §3: by default commit only
when asked (or when project policy says so) and never push unless asked or the
project enables auto-push.

---

# 4. HUMAN SAFETY GATES

Stop and ask before genuinely high-risk actions, at minimum:

- deleting production or canonical data, or irreplaceable project assets,
- rewriting Git history or force-pushing,
- irreversible migrations without a validated rollback,
- changing credentials, secrets, authentication or security ownership,
- anything that spends money or materially raises spending,
- deleting production infrastructure,
- destructive actions whose target is ambiguous.

At a gate: stop before acting, state the exact risk and the proposed action,
ask only the minimum decision. Prefer reversible operations.

---

# 5. COST AND EFFORT

Use the cheapest sufficient model, effort, workflow and number of agents.
Start low; escalate only when complexity, risk, uncertainty or a failed cheaper
attempt justifies it. Avoid rereading large files, repeating unchanged audits
and unnecessary subagents. Historical model/effort notes in project files are
advisory only.

---

# 6. AUTHOR / REVIEWER

One task has one primary author. Material work (architecture-sensitive,
production-affecting, migrations, security-sensitive) may get an independent
review that inspects actual repository evidence, not the author's summary. No
review ceremony for trivial, reversible work.

---

# 7. GIT AND EVIDENCE

Git and repository state are the durable truth. Before material work establish
root, branch, HEAD, working-tree and upstream state. Do not overwrite
unexplained work or silently absorb unrelated changes. Completion claims rest
on state, diffs, tests and evidence, not narrative. Never store a
self-referential "current HEAD" in tracked files.

---

# 8. SESSION LIFECYCLE

If the project has a `.ai/` directory, `.ai/STATE.md` is the canonical handoff
(current state + an explicit Exact Next Action) and `.ai/SESSION-LOG.md` is the
append-only history.

- `START` (or "start session"): restore state, reconcile with Git, determine the
  Exact Next Action, continue automatically when safe and unambiguous.
- `END` (or "finish session"): validate, update STATE.md and the session log,
  leave an exact resumable next action, verify final Git state.

The words inside ordinary sentences are not triggers. Procedure:
`LIFECYCLE-CONTEXT.md`. Chat history is never the only source of continuity.

---

# 9. SKILLS AND TOOLS

Selective use only. Do not invoke skills, subagents or elaborate workflows
merely because they exist; use them when they materially improve the result,
and never above project or global governance.

---

# 10. UNEXPECTED STATE

When actual state differs from expected: inspect, reconcile reversible
mechanical issues when scope is clear, preserve unexplained work, never hide
failed tests or partial work. Escalate only when consequences may be
destructive, scope is ambiguous, or a safety gate is reached.

---

# 11. DEFINITION OF DONE

Complete only when the applicable subset holds: scope implemented, relevant
checks pass, acceptance criteria met, no unrelated changes, Git state
understood, state records updated when needed, blockers and follow-ups
recorded, next session can reproduce the result. Code written is not
completion.

---

# 12. LANGUAGE

Reply in the language the user writes in. Prompts and handoffs for other AI
agents default to clear technical English. Project content (UI copy,
localization, documents) keeps the project-defined language; code identifiers
follow project standards.
