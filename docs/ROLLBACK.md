# Rollback, uninstall and what they do

Every install or update that changes something first records an undo entry in
`<claude-dir>/ai-governance-kit-backups/<timestamp>/` (default claude-dir: `~/.claude`; Windows `%USERPROFILE%\.claude`):
a copy of every file or folder it replaces, plus a `manifest.json`. A run that changes nothing creates no entry.

```
python3 install.py --list-backups          # undo entries, oldest first
python3 install.py --rollback --dry-run    # preview
python3 install.py --rollback              # undo the most recent change
python3 install.py --rollback 20261104-172740   # undo a specific entry
```
(Windows: `py -3`.)

## Exact semantics
- **One rollback undoes one change** (the most recent install or update). It does not "install an older version"; it puts back the files as they were
  before that run, which after an update are the previous kit version's files. The undone entry is renamed `*.rolled-back` and is not used again.
- **Full uninstall = repeat `--rollback`** until `--list-backups` is empty. That removes everything the kit created (`ai-governance/`, the kit's rule file, `skills/ponytail`,
  the managed block in `CLAUDE.md`, the hook entry) and restores what existed before.
- **Your later edits to `CLAUDE.md` and `settings.json` are kept.** If either file changed after the kit wrote it, rollback removes only the kit's managed block / hook entry instead of restoring an old copy.
- **Kit folders are removed as a whole.** If you customized a file inside `ai-governance/`, copy it first; rollback restores the pre-kit state of that folder (usually "absent").
- Other files in your Claude config (your skills, rules, settings, authentication) are never read, changed or removed by rollback.
- A failed install undoes itself automatically before exiting.
- Updates keep a file you customized (and say so); `install.py --force` replaces it after backing it up, and a rollback then restores your customized file.

## Manual rollback (no Python needed)
1. Open `~/.claude/CLAUDE.md`, delete the lines from `<!-- BEGIN AI-GOVERNANCE-STARTER-KIT` to `<!-- END AI-GOVERNANCE-STARTER-KIT -->`.
2. Delete `~/.claude/ai-governance/`, `~/.claude/rules/ai-governance-coding.md`, `~/.claude/skills/ponytail/` (only if it contains `.ai-governance-kit`).
3. If you used `--hooks`: remove the `UserPromptSubmit` entry whose command contains `ai-governance/hooks/session-lifecycle-trigger.py` from `~/.claude/settings.json`.
4. Restart VS Code / Claude Code. The `ai-governance-kit-backups/` folder can then be deleted.
