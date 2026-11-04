#!/usr/bin/env python3
"""Bootstrap project-level governance (AI Governance Starter Kit).

  python3 ~/.claude/ai-governance/bootstrap-project.py [DIR] [--name N] [--description D] [--dry-run]

Creates CLAUDE.md and .ai/STATE.md, .ai/SESSION-LOG.md in DIR (default: current
directory) from the kit templates. Never overwrites an existing file. Does not
copy global rules: they are inherited automatically from the user-level
CLAUDE.md.
"""
import argparse
import sys
import time
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent / "templates" / "project"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", nargs="?", default=".")
    ap.add_argument("--name")
    ap.add_argument("--description", default="TODO: one line describing this project.")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    root = Path(a.dir).expanduser().resolve()
    if root == Path.home().resolve():
        print("Refusing to bootstrap your home directory; pass a project directory.")
        return 1
    subs = {"{{PROJECT_NAME}}": a.name or root.name, "{{ONE_LINE_DESCRIPTION}}": a.description,
            "{{DATE}}": time.strftime("%Y-%m-%d")}
    for src in sorted(p for p in TEMPLATES.rglob("*") if p.is_file()):
        dst = root / src.relative_to(TEMPLATES)
        if dst.exists():
            print("skip    %s (already exists, left unchanged)" % dst.relative_to(root))
            continue
        print("%s %s" % ("would create" if a.dry_run else "create ", dst.relative_to(root)))
        if not a.dry_run:
            text = src.read_text(encoding="utf-8")
            for k, v in subs.items():
                text = text.replace(k, v)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(text, encoding="utf-8")
    if not (root / ".git").exists():
        print("note: %s is not a Git repository (run `git init` if you want one)" % root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
