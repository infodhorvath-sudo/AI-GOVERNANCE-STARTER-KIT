# AUTONOMY / GIT / SAFETY MODULE

On-demand module of the Global AI Governance (see `GLOBAL-RULES.md`). Read when
committing, pushing, merging, deploying, handling destructive or
safety-sensitive actions, or reconciling unexpected repository state.

# 1. AUTONOMY ENVELOPE

Within a clear task scope, work autonomously on reversible, routine steps:
inspect files and Git state, edit scoped files, create branches/worktrees, run
builds, tests, lint and typechecks, fix errors, stage scoped changes.

Do not ask for approval of mechanical steps that tests, Git state or project
rules can decide.

# 2. HUMAN SAFETY GATES

Stop and ask before: deleting production/canonical data or irreplaceable
assets; history rewrites or force-pushes; irreversible migrations without
rollback; credential/secret/auth changes; spending money; deleting production
infrastructure; destructive actions with an ambiguous target.

State the exact risk and proposed action; ask for the minimum decision.

# 3. GIT DISCIPLINE

Before material work establish: repo root, branch/worktree, HEAD, working-tree
state, upstream state. Do not overwrite unexplained work or absorb unrelated
changes. For substantial or risky work prefer an isolated branch.

Commits: clear scope, no unrelated changes, meaningful message.

**Defaults of this kit (deliberately conservative):**

- Commit only when the user asks or the project's `CLAUDE.md` says commits at
  task closure are expected.
- Push only when the user asks or the project's `CLAUDE.md` enables
  auto-push. Never push mid-task, never force-push, never rewrite history.
- A project can enable auto-push by adding to its `CLAUDE.md`:
  `Auto-push: at task closure (validated, reviewed if required, scoped commit)
  push the current branch to its upstream and verify sync.`
  Even then: stop and report if the push is rejected, the branch diverged,
  secrets may be present, or the target is ambiguous.

After work verify the actual Git state (diff, status, tests), not a narrative.

# 4. UNEXPECTED STATE

Inspect the discrepancy; resolve reversible mechanical issues when scope is
clear; preserve unexplained work; never hide failed tests or partial work;
escalate only for destructive consequences, ambiguous ownership or a safety
gate.

# 5. DEFINITION OF DONE

Scope implemented; relevant checks pass; acceptance criteria met; no unrelated
changes; Git state understood; state records updated; commit/push per project
policy; follow-ups recorded; next session can reproduce the result.
