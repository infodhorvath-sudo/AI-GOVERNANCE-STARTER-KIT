#!/usr/bin/env python3
"""
UserPromptSubmit hook: deterministic Session Lifecycle trigger.

Detects exact standalone START/END commands (or a short, explicitly
supported list of aliases) and injects additionalContext instructing
Claude to run the START/END SESSION protocol from the Global AI Governance.

Stdlib only. No network, no LLM, no subagent, no project mutation.
Must exit 0 and print nothing for any non-trigger prompt.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

START_EXACT = {"start"}
END_EXACT = {"end"}

START_ALIASES = {"start session"}

END_ALIASES = {"finish", "finish session", "end session"}

TRAILING_PUNCT = ".!?"


def normalize(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw)
    text = text.strip()
    text = text.strip('"').strip("'")
    text = text.strip()
    text = text.rstrip(TRAILING_PUNCT)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def extract_prompt(payload: dict) -> str:
    for key in ("prompt", "user_prompt", "message", "input"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def classify(normalized: str) -> Optional[str]:
    if not normalized:
        return None
    if normalized in START_EXACT:
        return "START"
    if normalized in END_EXACT:
        return "END"
    if normalized in START_ALIASES:
        return "START"
    if normalized in END_ALIASES:
        return "END"
    return None


END_CONTEXT = """SESSION_LIFECYCLE_END_TRIGGER

The user has explicitly issued the canonical END SESSION command.

This is NOT a conversational farewell.

Before replying to the user, execute the END SESSION protocol from the
user's Global AI Governance.
Read ~/.claude/ai-governance/modules/LIFECYCLE-CONTEXT.md for the full
procedure.

For the active project:

1. Load applicable global governance.
2. Load applicable project governance.
3. Inspect durable project state/handoff if available.
4. Inspect the latest relevant session log if available.
5. Inspect actual Git/workspace state.
6. Derive current branch, HEAD, upstream and dirty state from Git at runtime.
7. Finish already-implied safe mechanical work within the autonomy envelope.
8. Run relevant validation.
9. Resolve safe inconsistencies where project policy permits.
10. Update durable logical state.
11. Append the session log.
12. Commit and push accepted routine changes where governance permits.
13. Merge/deploy only if already authorized by applicable project policy and
    relevant gates pass.
14. Verify final Git/workspace state.
15. Leave an exact resumable next action.

Do NOT merely say goodbye or acknowledge that the session is ending.

Do NOT ask the user to manually perform routine Git actions that fall
inside the autonomy envelope.

This project has adopted the Starter Kit lifecycle convention (.ai/STATE.md exists).
If the user has their own start/end workflow, follow theirs and do not run a second
procedure."""

START_CONTEXT = """SESSION_LIFECYCLE_START_TRIGGER

The user has explicitly issued the canonical START SESSION command.

Before beginning normal implementation, execute the START SESSION protocol
from the user's Global AI Governance.
Read ~/.claude/ai-governance/modules/LIFECYCLE-CONTEXT.md for the full
procedure.

For the active project:

1. Load applicable global governance.
2. Load applicable project governance.
3. Read durable STATE/handoff if available.
4. Read the latest relevant session-log entry if available.
5. Inspect actual Git/workspace state.
6. Derive branch, HEAD, upstream and dirty state from Git at runtime.
7. Compare durable logical state with actual repository state.
8. Reconcile safe discrepancies autonomously where policy permits.
9. Determine the current objective.
10. Determine the exact next action.
11. Determine AUTHOR/REVIEWER only when materially required.
12. Select the cheapest sufficient model/effort.
13. Resume from the recorded next action.

Do NOT ask the user to reconstruct prior context when durable state
already contains it.

Do NOT persist "current HEAD" as a self-referential field inside tracked
STATE. Runtime Git facts must continue to come from Git itself.

This project has adopted the Starter Kit lifecycle convention (.ai/STATE.md exists).
If the user has their own start/end workflow, follow theirs and do not run a second
procedure."""


def main() -> int:
    try:
        raw_stdin = sys.stdin.read()
        payload = json.loads(raw_stdin) if raw_stdin.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return 0

    if not isinstance(payload, dict):
        return 0

    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not Path(cwd, ".ai", "STATE.md").is_file():
        return 0

    prompt = extract_prompt(payload)
    normalized = normalize(prompt)
    trigger = classify(normalized)

    if trigger is None:
        return 0

    context = END_CONTEXT if trigger == "END" else START_CONTEXT

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
