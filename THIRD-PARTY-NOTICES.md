# Third-party notices

This repository is licensed under the MIT License (see [LICENSE](LICENSE)), except for the
component below, which keeps its own copyright and license.

## Ponytail skill

- Path: `payload/skills/ponytail/` (`SKILL.md` unmodified, plus its `LICENSE`)
- Upstream: https://github.com/DietrichGebert/ponytail
- Version: plugin 5.3.3, upstream commit `96608e078b2d5ea607c5c3b8b5a54d1c1fba6846`
- License: MIT, Copyright (c) 2026 DietrichGebert (full text in `payload/skills/ponytail/LICENSE`)
- Only the skill file is vendored; upstream hooks, companion skills and plugin code are not included.

The kit's installer copies this directory to `~/.claude/skills/ponytail/` together with its license.
No other third-party code is included; the kit uses only the Python standard library.
