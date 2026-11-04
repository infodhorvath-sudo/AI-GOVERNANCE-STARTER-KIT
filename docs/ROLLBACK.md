# Rollback

Every install that changes something first backs up what it replaces to
`<claude-dir>/ai-governance-kit-backups/<timestamp>/` (default claude-dir:
`~/.claude`; `%USERPROFILE%\.claude` on Windows) together with a `manifest.json`.
An install that changes nothing creates no backup.

```
python3 install.py --list-backups          # see backups
python3 install.py --rollback --dry-run    # preview
python3 install.py --rollback              # undo the most recent change
python3 install.py --rollback 20261104-172740   # undo a specific one
```

Rollback restores every replaced file/dir byte-for-byte, deletes everything the
kit newly created (and directories it created, if empty), and renames the
backup to `*.rolled-back`.

## Manual rollback (no Python needed)

1. Open `~/.claude/CLAUDE.md`, delete the lines from
   `<!-- BEGIN AI-GOVERNANCE-STARTER-KIT` to `<!-- END AI-GOVERNANCE-STARTER-KIT -->`.
2. Delete `~/.claude/ai-governance/`, `~/.claude/rules/ai-governance-coding.md`,
   `~/.claude/skills/ponytail/` (only if it contains `.ai-governance-kit`).
3. If you used `--hooks`: remove the `UserPromptSubmit` entry whose command
   contains `ai-governance/hooks/session-lifecycle-trigger.py` from
   `~/.claude/settings.json` (or copy your original back from the backup folder).
4. Restart VS Code / Claude Code.
