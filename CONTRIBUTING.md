# Contributing

Small, focused contributions are welcome. The goal of the kit is to stay lightweight.

## Report a bug / suggest an idea
Open an issue (templates provided). For bugs include OS, Python version, the command you ran and the output of
`python3 verify.py`. For security problems see [SECURITY.md](SECURITY.md) instead.

## Pull requests
1. Fork, create a branch, keep the change small and on one topic.
2. Run `python3 verify.py` (must show 0 FAIL).
3. If you changed any shipped file: `python3 tools/make-release.py` to refresh `RELEASE-MANIFEST.json`, and commit it. Maintainers build the lightweight install ZIP with `python3 tools/make-release.py --zip OUT` (decorative images omitted, own manifest).
4. Describe what changed and how you tested it.

## Expectations
- Python 3.8+, standard library only. No new dependencies, services, telemetry or background processes.
- Installer changes must keep: dry-run writes nothing, backup before change, no overwrite of user content,
  idempotent re-install, working `--rollback`. Add or extend a scenario in `verify.py` for new behavior.
- Text files use LF (see `.gitattributes`). No absolute personal paths, secrets or personal data in any file.
- Docs must describe actual behavior. Do not claim support for an assistant, OS or feature that is not implemented and tested.
- New rules must be generic, short and project-neutral.

## Compatibility
Primary target: Claude Code (CLI and VS Code extension) on macOS. Linux and Windows are statically validated;
real-machine reports are very welcome.
