# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Versions follow [SemVer](https://semver.org/).

## [1.0.1] - 2026-11-04
### Fixed
- **Rules silently not loaded when the Claude config path contains a space** (typical for Windows profile folders that contain a space): the managed `@import` was an absolute path and a space ended it. The import now uses the documented `~/` form under the home folder (verified in Claude Code with spaces and Unicode) and a backslash-escaped absolute path elsewhere. Existing installs are migrated in place by the next `install.py`.
- Updates no longer overwrite files you customized: the installer records what it installed (`ai-governance/.kit-state.json`); a changed file is kept and reported, `--force` replaces it (backup kept); files you added inside kit folders are never removed; files dropped by a newer release are removed only if unmodified.
- Installer messages are accurate ("refreshed" vs "added", undo-record wording).
### Added
- `verify.py` level 4 now asks the real Claude Code CLI what it loads (`/context`, offline, no login) and whether the hook fires; sandbox scenarios for customization, unusual paths (spaces/Unicode) and a real-Claude-Code load test.
- `docs/INSTALLATION-GUIDE.md`, `docs/assets/` (renderings of real terminal output), README "Get started in 4 steps", acceptance checklist in `docs/VERIFY-IN-VSCODE.md`.
### Changed
- Version and canary are `1.0.1` / `AIGOV-KIT-1.0.1-LOADED`. The canary is the installed-kit version marker, so after an update it also proves the new rules were loaded.

## [1.0.0] - 2026-11-04
First public release.
### Added
- MIT `LICENSE`, `THIRD-PARTY-NOTICES.md`, `CONTRIBUTING.md`, `SECURITY.md`, issue and pull request templates.
- `install.py` (macOS/Linux/Windows): dry-run, backup before change, safe merge into `~/.claude/CLAUDE.md`
  and `settings.json`, idempotent re-install, update over an earlier install, `--rollback`, automatic undo on failure.
- Global rules (`GLOBAL-RULES.md`) and three on-demand modules: lifecycle, Git/safety, cost/review.
- User-level coding rule, vendored Ponytail skill (MIT), optional START/END hook (`--hooks`).
- Project bootstrap (`bootstrap-project.py`) with `CLAUDE.md` and `.ai/` templates.
- `verify.py` with separate package / sandbox / target / runtime levels and explicit statuses.
- `RELEASE-MANIFEST.json` (SHA-256), `.gitattributes` (LF), `tools/make-release.py`.
