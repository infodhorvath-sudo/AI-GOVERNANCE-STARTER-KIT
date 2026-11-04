# What is automatic and what needs setup

| Feature | Status | How it becomes active |
|---|---|---|
| Global rules (`GLOBAL-RULES.md`: authority, safety gates, autonomy, cost, Git, definition of done, Ponytail coding standard) | **Automatic** | Imported by the managed block in `~/.claude/CLAUDE.md`; loaded at the start of every Claude Code session in every project, existing or new. Needs a *new* session after install. |
| Coding rule `rules/ai-governance-coding.md` | **Automatic** | Claude Code loads `~/.claude/rules/*.md` at session start. |
| Modules (lifecycle, Git/safety, cost/review) | **On demand** | Not preloaded. The rules tell Claude to read one only when the task needs it. |
| `ponytail` skill | **On demand** | Discovered from `~/.claude/skills/`; only its description is visible until a coding task matches (or you type `/ponytail`). Not an always-on mode. |
| START / END commands | **Works without setup**, hook optional | Without the hook, typing `START` / `END` relies on the rules in context. With `install.py --hooks`, a `UserPromptSubmit` hook injects an explicit reminder when the prompt is exactly `start` / `end` / `finish`. |
| Project governance (`CLAUDE.md`, `.ai/STATE.md`) | **Optional per project** | `python3 ~/.claude/ai-governance/bootstrap-project.py <dir>`. |
| Auto-commit / auto-push | **Off by default** | A project enables it in its own `CLAUDE.md` (see the template). Deliberately more conservative than the original system. |
| Plugins, MCP servers, agents/subagents | **Not installed** | The original system had no portable agents; none are shipped. Nothing is installed from the network. |

The managed block imports the rules by an absolute path generated on *your* machine at install time
(nothing machine-specific ships in the kit). Imports are limited to 4 levels; the kit uses 1.
User-level imports need no approval dialog (documented).

Nothing here is assumed to work because files were copied: `verify.py` checks
the files, `verify.py --live` asks Claude whether the rules were really loaded.
