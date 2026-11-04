# Acceptance checklist (about 5 minutes)

Run `python3 verify.py` first. Then use a **temporary project** (never a real one) for the manual part. Nothing here runs destructive Git commands.

## What proves what
| Check | Proves | Does not prove |
|---|---|---|
| `verify.py` levels 1-3 | The kit is intact and installed correctly; imports resolve | That Claude loads anything |
| `verify.py` level 4 (offline loader check, real Claude Code CLI, no login) | The CLI loads your user `CLAUDE.md`, the imported rules, the rule file, a project `CLAUDE.md`, the `ponytail` skill, and runs the hook | That the VS Code extension does the same; that the model follows the rules |
| Canary question | The kit's rules file reached the model's context. The canary is the **installed kit version marker** (so after an update it shows the new version) | That every module, skill or hook works |
| Rule questions (below) | Specific rule *content* is in context and the project rule is reported as winning | That the model will always comply: rules are advisory |

## Part A: automatic (no login)
```
python3 verify.py
```
Level 4 should list `PASS` for: user CLAUDE.md, GLOBAL-RULES.md import, user rule, project CLAUDE.md, ponytail skill (and the hook if you used `--hooks`).
`NOT TESTED` means the `claude` command is not on your PATH, not a failure.

## Part B: manual, in VS Code
Restart VS Code first (new Claude Code session). Create a throwaway project:
```
mkdir kit-acceptance && cd kit-acceptance
python3 ~/.claude/ai-governance/bootstrap-project.py . --name "Kit Acceptance"
```
(Windows: `py -3 "%USERPROFILE%\.claude\ai-governance\bootstrap-project.py" . --name "Kit Acceptance"`.) Open the folder in VS Code and start a **new** Claude Code conversation.

| # | You ask / do | Expected | Establishes |
|---|---|---|---|
| 1 | *What is the AI Governance canary?* | `AIGOV-KIT-1.0.1-LOADED` | Global rules loaded in the extension |
| 2 | *Under your global governance rules, may you run `git push` without me asking?* | No: only when asked or when the project enables auto-push | A specific rule's content is in context (not just the marker) |
| 3 | Type `/` and look for **ponytail**; or ask *Which skill in your list covers lean coding?* | `ponytail` appears | Skill discovered in the extension |
| 4 | Add to the project's `CLAUDE.md`: `Project rule: commits are allowed at task closure without asking.` Start a new conversation and ask *May you commit at task closure without asking in this project?* | Yes, per the project rule (it overrides the global default) | Project instructions coexist with, and take precedence over, global ones. Nothing is committed |
| 5 | (only if installed with `--hooks`) Send exactly `start` | Claude begins the START procedure and reads `.ai/STATE.md` | Hook text reached the model |
| 6 | `python3 install.py --rollback --dry-run` | Lists the files it would restore or remove; changes nothing | Rollback is available |

Cleanup: delete the `kit-acceptance` folder. If steps 1-4 pass, the VS Code integration is confirmed on your machine; please report results (and VS Code / extension versions) in an issue.
If step 1 fails: restart VS Code, use a new conversation, check `~/.claude/CLAUDE.md` contains the `AI-GOVERNANCE-STARTER-KIT` block, run `/memory` or `/context` to see which files are loaded.

## `verify.py --live` (optional)
Three tiny Haiku requests with your own login: canary visible in a new project, project canary alongside, canary visible in a bare project. It covers the model-level part of steps 1 and 4 for the CLI, not the extension.

## What is documented vs. tested
Anthropic documents user-level `CLAUDE.md`, `@` imports (no approval dialog at user level), `~/.claude/rules/*.md`, user skills, hooks in `settings.json`, `CLAUDE_CONFIG_DIR`,
and `%USERPROFILE%\.claude` on Windows (code.claude.com/docs). Sharing every one of these with the VS Code extension is explicitly documented only for `settings.json`, which is why Part B exists.
