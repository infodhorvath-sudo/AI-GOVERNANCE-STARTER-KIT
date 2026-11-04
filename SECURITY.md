# Security policy

## Reporting a vulnerability
Please report privately using GitHub's **Report a vulnerability** button on the
[Security tab](https://github.com/infodhorvath-sudo/AI-GOVERNANCE-STARTER-KIT/security/advisories/new)
of this repository. Do not open a public issue for security problems.

This is a small, volunteer-maintained project: expect an acknowledgement on a best-effort basis.

## Scope and design
The installer only writes inside your Claude config directory, backs up what it replaces, never reads
or copies authentication files, makes no network calls and sends no telemetry. The optional hook only prints
text. Issues worth reporting: the installer or hook touching files or data outside that scope, unsafe merging
of `settings.json`/`CLAUDE.md`, or a way the kit could leak or destroy user data.

Not a vulnerability: the rules being advisory. They are prompt instructions and cannot guarantee how an AI model behaves.
