# Manual verification in VS Code (2 minutes)

Run `python3 verify.py` first (file checks). This page proves the part files cannot:
that Claude Code actually loads the rules.

1. **Restart VS Code** (or `Developer: Reload Window`) so Claude Code starts a *new* session.
2. **Global rules load (canary).** Open any folder, open Claude Code and ask:
   *"What is the AI Governance canary?"* -> expected answer: `AIGOV-KIT-1.0.0-LOADED`.
   Optional: `/memory` lists the loaded CLAUDE.md files; `/context` shows the memory files in use.
3. **New project inherits.** Make an empty folder, open it in VS Code, ask the same question.
   Same answer, with no project files present.
4. **Project rules work alongside.** In that folder run
   `python3 ~/.claude/ai-governance/bootstrap-project.py . --name Demo` (Windows: `py -3 %USERPROFILE%\.claude\ai-governance\bootstrap-project.py . --name Demo`),
   add the line `Project canary code: ZEBRA-1` to `CLAUDE.md`, start a new Claude Code
   session there and ask: *"Governance canary and project canary code?"* -> both.
5. **Skill discovered.** Type `/` and look for `ponytail`.
6. **Hook (only if installed with `--hooks`).** Send exactly `start`. Claude should begin the
   START procedure (read `.ai/STATE.md` if present, check Git).
7. **Existing projects unchanged.** `git status` in an existing repo is clean: the installer
   only writes inside the Claude config directory.

If step 2 fails: run `python3 verify.py` (is the kit installed?), check that `~/.claude/CLAUDE.md`
contains the managed block, and that you restarted VS Code. Automated equivalent of steps 2-4
(your own login, 3 tiny Haiku requests): `python3 verify.py --live`.

## What is documented vs. tested
Documented by Anthropic (code.claude.com/docs): user-level `CLAUDE.md` loads in every project;
`@path` imports (user-level imports need no approval dialog); `~/.claude/rules/*.md`; user skills in
`~/.claude/skills/`; hooks in `settings.json`; `CLAUDE_CONFIG_DIR`; Windows config dir `%USERPROFILE%\.claude`.
Whether the VS Code extension shares every one of these with the CLI is only documented for
`settings.json`, which is why this manual check exists.
