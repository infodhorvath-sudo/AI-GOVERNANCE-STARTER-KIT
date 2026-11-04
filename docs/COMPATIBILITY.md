# Compatibility with your own setup

The Starter Kit is a **baseline**, not an authority above you. Its rules are defaults: when your current request, your project, or your own personal instructions, skills and workflows cover the same matter, they win and the kit's rule is only the fallback. Claude Code documents no formal precedence between instruction files, so the kit says this in its own rules instead of assuming one.

## Language: multilingual by default
Any language Claude supports works; there is no list and nothing to configure. In this order:
1. **Your explicit request in the conversation**, e.g. "Please answer in Spanish" / «Отвечай по-русски» / 「日本語でお願いします」.
2. **A language preference you already have**, in your own `~/.claude/CLAUDE.md` or rules, or in the project's `CLAUDE.md` (e.g. "Always respond in English"). The kit never overrides it and never adds a competing language rule.
3. **Otherwise the language of your message** (for mixed messages, the dominant one).
4. If it is genuinely unclear, the conversation's established language; switch the moment you ask.

Code, commands, identifiers and file paths are never translated. The language you chat in can differ from the language of code comments, documentation or UI text. Example project convention, put in that project's `CLAUDE.md`: *"Talk to me in English; write documentation and user-facing text in Spanish."* Each artifact then follows its own rule.
These are instructions to a language model: they steer behavior, they cannot guarantee it. Check it yourself with the manual test in [VERIFY-IN-VSCODE.md](VERIFY-IN-VSCODE.md).

## Session handoff (`start` / `end`) is opt-in
- The kit's handoff convention (`.ai/STATE.md`, `.ai/SESSION-LOG.md`, the words `START`/`END`) applies **only in a project that contains `.ai/STATE.md`**, i.e. one created with `bootstrap-project.py` or adopted by you.
- Everywhere else `start` and `end` are ordinary words. The kit never creates `.ai/` because you typed them.
- If you already have your own `start`/`end` skills or commands, or workflow files such as `QUEUE.md` and `HANDOFF.md`, yours take precedence; the kit does not run a second procedure after or instead of yours, and never renames or removes your skills.
- The optional hook (`install.py --hooks`) is silent unless the prompt is exactly `start`/`end`/`finish` **and** the current project has `.ai/STATE.md`.
- To opt in for a project: `python3 ~/.claude/ai-governance/bootstrap-project.py .`. To opt out: do not bootstrap (or delete its `.ai/STATE.md`).

## What the installer does about it
It never changes your skills, rules or instructions. If you already have `skills/start`, `skills/end`, `commands/start.md` or `commands/end.md`, the dry run prints an informational `NOTE:` (names only, never contents). It does not try to interpret your own instructions, so a personal "always respond in English" line is not detected: it needs no handling, because the kit yields to it.

## If two instructions still conflict
Tell Claude which one you mean ("for this project, follow my own workflow"), or write it once where it applies: your `CLAUDE.md` for everything, the project's `CLAUDE.md` for one project. The kit's rules are asked to follow that and, when two of your own instructions disagree and it is unclear, to ask you once rather than guess.

## Updating from v1.0.1
`git pull --ff-only && python3 install.py --dry-run && python3 install.py`. Kit files are replaced (your edits are kept and reported); the language rule and the opt-in handoff behavior change; your `CLAUDE.md` text, settings and skills are untouched. The canary becomes `AIGOV-KIT-1.0.2-LOADED` (it equals the installed version). `--rollback` returns to v1.0.1 exactly.
