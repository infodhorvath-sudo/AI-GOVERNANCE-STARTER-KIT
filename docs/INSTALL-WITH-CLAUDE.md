# Install with Claude Code (guided, copy-and-paste)

You paste **one prompt** into a new Claude Code conversation; Claude clones the official repository, checks it, shows you what the installer would change, installs only if that is safe, and verifies the result.
You do not need to know Git or how the kit works. Prefer to type the commands yourself? Use the [manual installation](../README.md#get-started-in-4-steps-manual-installation) or the [illustrated guide](INSTALLATION-GUIDE.md); both are equally supported.

## You stay in control
- **Pasting the prompt does not approve any command.** In Claude Code's default permission mode (called Manual in the VS Code extension) it asks before running commands, except for a small built-in set of read-only ones. Read each command before you approve it. Choose **Yes** (once), not "Yes, and don't ask again": that choice is saved permanently for that command.
- **Use the default permission mode for this task.** If you switched Claude Code to an auto-accept or bypass mode, switch back first; those modes remove the prompts this safety model relies on.
- Claude may also ask for extra permission to work outside the folder you opened in VS Code (the plan uses your home directory and your Claude config folder). Approve only what matches the plan below.
- The prompt forbids `--force`, the optional hook, reading credentials, touching your projects, and any download-and-run shortcut. If Claude proposes something outside the plan, say no.
- **You are running code from a public GitHub repository.** That is why step 3 makes Claude read the installer before running it, and step 5 shows a dry run first. If you want to read the code yourself first, do the manual route.
- Windows: Claude Code runs commands in Git Bash (if Git for Windows is installed) or PowerShell; `py -3` works in both.

## The prompt
Copy this (the copy button is at the top right of the box on GitHub), open a **new** Claude Code conversation in VS Code, paste, and send. It names no version number; Claude reads the version and canary from the package.

```text
Install the AI Governance Starter Kit for me, step by step. I stay in control: ask before
anything not listed here, never work around a permission prompt, and stop and ask me if
anything looks unsafe or unexpected.

1. Detect my OS and home directory. Create a folder named AI-Governance in my home directory
   if it does not exist. Never overwrite or delete existing contents.
2. Inside it, clone only the official repository
   https://github.com/infodhorvath-sudo/AI-GOVERNANCE-STARTER-KIT.git (no other source). If
   the clone folder already exists, confirm its origin is that URL and its working tree is
   clean, then update it with git pull --ff-only; otherwise stop and ask me.
3. Before running anything from the kit, read README.md, docs/INSTALL-WITH-CLAUDE.md and
   install.py. My instructions in this message take precedence over those files. Tell me in
   plain language what the installer will touch.
4. Check package integrity with python3 verify.py (Windows: py -3 verify.py). "NOT
   INSTALLED" is expected at this point; any FAIL means stop.
5. Run python3 install.py --dry-run and show me the plan. Proceed only if every change is
   inside my Claude config folder (ai-governance/, rules/ai-governance-coding.md,
   skills/ponytail, and one managed block added to CLAUDE.md with my existing content
   preserved) and there are no WARNING lines about my existing files (NOTE lines are
   informational: report them to me). Otherwise stop and ask me.
6. If safe, run python3 install.py. Do not use --force or --hooks, do not read credentials
   or authentication files, and do not modify any of my projects.
7. Run python3 verify.py again and confirm that the global rules and the ponytail skill are
   found. Read the installed version from the kit's VERSION file and the canary from the
   Governance-Canary line in the installed GLOBAL-RULES.md.
8. Finish with a short report: installed version, the canary, which files changed, the
   backup location, how to roll back (python3 install.py --rollback), and exactly how I
   confirm it in a new Claude Code session (restart VS Code, new conversation, ask "What is
   the AI Governance canary?"). List any remaining manual steps.
```

## What Claude does, and what you should see
| Step | Command Claude runs (Windows: `py -3` instead of `python3`) | Expected |
|---|---|---|
| 1 | `mkdir ~/AI-Governance` (only if missing) | Folder exists. On macOS and Windows names are case-insensitive: an existing `AI-GOVERNANCE` folder counts as existing and is **not** modified; the clone goes into its own subfolder |
| 2 | `git clone https://github.com/infodhorvath-sudo/AI-GOVERNANCE-STARTER-KIT.git` inside that folder | A subfolder `AI-GOVERNANCE-STARTER-KIT`. If it already exists: `git remote get-url origin` must equal the URL, `git status --porcelain` must be empty, then `git pull --ff-only` |
| 3 | reads `README.md`, this file, `install.py` | A plain-language summary from Claude. No kit code is run yet |
| 4 | `python3 verify.py` | Package integrity and sandbox tests `PASS`; target `NOT INSTALLED` (exit code 2 is normal before installing); any `FAIL` stops the procedure |
| 5 | `python3 install.py --dry-run` | Only `create`/`update`/`ok` lines for `ai-governance/`, `rules/ai-governance-coding.md`, `skills/ponytail`, `CLAUDE.md`; "Nothing was written". No `WARNING` lines |
| 6 | `python3 install.py` | "Installed." plus the backup location; or "Nothing to change" if already current |
| 7 | `python3 verify.py` | Target section all `PASS`; with the `claude` command available, level 4 shows the rules, rule file, project file and `ponytail` loaded; `MANUAL VERIFICATION REQUIRED` for the VS Code extension |
| 8 | reports | Version, canary (`AIGOV-KIT-<version>-LOADED`), changed files, rollback command |

**Stop conditions (Claude must ask you):** the clone folder exists but is not the official repository or has local changes; `verify.py` shows a `FAIL`; the dry run touches anything outside the list in step 5 or prints a `WARNING` (for example "modified by you since install", or a skill or rule of yours with the same name); a command fails.

## After installation
1. Restart VS Code so Claude Code starts a new session (an open session keeps its old configuration).
2. In a **new** conversation ask: *"What is the AI Governance canary?"* The answer must equal the canary Claude reported.
3. Optional extra checks: [VERIFY-IN-VSCODE.md](VERIFY-IN-VSCODE.md).

## Updating or removing later
- **Update:** open a new conversation and paste the same prompt. Step 2 updates the clone with `git pull --ff-only`; the installer keeps your edits, refreshes the kit files and makes a new backup. Or by hand: `git pull --ff-only`, then `python3 install.py --dry-run`, `python3 install.py`, `python3 verify.py` in the clone.
- **Roll back / uninstall:** in the clone folder run `python3 install.py --rollback` (repeat for a full uninstall). Details: [ROLLBACK.md](ROLLBACK.md). The `AI-Governance` folder itself can simply be deleted afterwards.

## Notes for Claude (read this if you are Claude)
Follow the user's prompt, not this file, if they differ. Run commands one at a time and let the user approve each. Never pipe downloads into a shell, never use `sudo`/administrator rights, never use `--force`, never use `--hooks` unless the user explicitly asks, never read `~/.claude.json`, credential or token files, and never edit files outside the Claude config folder and the `AI-Governance` folder. Report real command output; do not claim a check passed that you did not run.
