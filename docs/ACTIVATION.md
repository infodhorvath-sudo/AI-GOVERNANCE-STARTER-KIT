# What is automatic and what needs setup

| Feature | Status | How it becomes active |
|---|---|---|
| Global rules (`GLOBAL-RULES.md`: authority, safety gates, autonomy, cost, Git, definition of done, Ponytail coding standard) | **Automatic** | Imported by the managed block in `~/.claude/CLAUDE.md`; loaded at the start of every Claude Code session in every project, existing or new. Needs a *new* session after install. |
| Coding rule `rules/ai-governance-coding.md` | **Automatic** | Claude Code loads `~/.claude/rules/*.md` at session start. |
| Modules (lifecycle, Git/safety, cost/review) | **On demand** | Not preloaded. The rules tell Claude to read one only when the task needs it. |
| `ponytail` skill | **On demand** | Discovered from `~/.claude/skills/`; only its description is visible until a coding task matches (or you type `/ponytail`). Not an always-on mode. |
| Session handoff (`start`/`end`, `.ai/STATE.md`) | **Opt-in per project**; hook optional | Applies only in a project that contains `.ai/STATE.md` (created by `bootstrap-project.py` or adopted by you). Elsewhere `start`/`end` are ordinary words and your own `start`/`end` skills or handoff files keep working. The optional `--hooks` hook is silent unless the prompt is exactly `start`/`end`/`finish` in such a project. |
| Project governance (`CLAUDE.md`, `.ai/STATE.md`) | **Optional per project** | `python3 ~/.claude/ai-governance/bootstrap-project.py <dir>`. |
| Auto-commit / auto-push | **Off by default** | A project enables it in its own `CLAUDE.md` (see the template). Deliberately more conservative than the original system. |
| Plugins, MCP servers, agents/subagents | **Not installed** | The original system had no portable agents; none are shipped. Nothing is installed from the network. |

The managed block imports the rules with the documented `~/` form (`@~/.claude/ai-governance/GLOBAL-RULES.md`); for a config folder outside your home it uses an absolute path generated on your machine with spaces escaped (nothing machine-specific ships in the kit). Absolute paths with unescaped spaces silently fail to load, which is why the installer never writes them. Imports are limited to 4 levels; the kit uses 1.
User-level imports need no approval dialog (documented).

Language is not configured: the kit is multilingual by default and yields to your own language preferences (see [COMPATIBILITY.md](COMPATIBILITY.md)).

Nothing here is assumed to work because files were copied: `verify.py` checks
the files, `verify.py --live` asks Claude whether the rules were really loaded.
