# COST / REVIEW / TOOLS MODULE

On-demand module of the Global AI Governance (see `GLOBAL-RULES.md`). Read when
choosing model/effort, deciding on independent review or subagents, or using
skills/plugins.

# 1. COST AND EFFORT

Use the cheapest sufficient model, effort, workflow and number of agents.

- Start at the lowest reasonable effort; escalate (low → medium → high) only when
  complexity, risk, uncertainty or a failed cheaper attempt justifies it.
- No premium model "to be safe"; no multiple agents when one suffices.
- Do not reread large files, repeat audits whose state has not changed, or run
  review for trivial mechanical work.
- Prefer targeted reads and diffs over loading whole repositories.
- Old model/effort recommendations in project files are advisory only.

Rough effort guide: Low = status checks, small docs/config edits, narrow
mechanical tasks. Medium = normal implementation, real bug fixes, multi-file
reasoning, material review. High = hard architecture, subtle or safety-critical
reasoning, failures after cheaper attempts.

# 2. AUTHOR AND REVIEWER

One task, one primary AUTHOR; no concurrent edits to the same scope unless
isolated parallel work is required.

When review is justified: author → validate → independent reviewer (inspects
actual repository evidence, not the author's report) → accept → commit/merge as
policy allows. Appropriate for architecture-sensitive, production-affecting,
migration, security-sensitive or critical-invariant changes. Skip for trivial,
low-risk, reversible work.

# 3. SKILLS, PLUGINS, SUBAGENTS

Use selectively. Ask whether a workflow materially improves the result before
paying for it. Do not run full planning/subagent/worktree/review chains for
simple tasks. Skills never override the user, project or global governance.
Load task-specific instructions only when the task needs them.

# 4. MULTI-AGENT PROJECTS

For a substantial new project or major workstream, decide up front: objective
and success condition, which roles are really needed, which workstreams can run
in parallel, the single author per mutable workstream, where independent
challenge or review pays off, how evidence is handed off, and the durable source
of truth. Multi-agent never means multi-author on one task, and every agent
needs a distinct purpose. Record topology changes that outlive the conversation
in the project's state files.
