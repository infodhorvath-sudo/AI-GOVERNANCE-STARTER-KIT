# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Versions follow [SemVer](https://semver.org/).

## [Unreleased]
### Added
- `docs/INSTALLATION-GUIDE.md`: illustrated step-by-step guide (clone in VS Code or ZIP, expected output, troubleshooting, update, uninstall) and `docs/assets/` terminal renderings of real output.
- README "Get started in 4 steps".
### Changed
- Installer wording only: clearer dry-run/install messages (no behavior change).

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
