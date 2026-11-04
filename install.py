#!/usr/bin/env python3
"""AI Governance Starter Kit installer (Python 3.8+, stdlib only).

Installs user-level governance for Claude Code (CLI and VS Code extension).

  python3 install.py --dry-run     show the plan, write nothing
  python3 install.py               install / update (idempotent)
  python3 install.py --hooks       also register the optional START/END hook
  python3 install.py --rollback    restore the state before the last change
  python3 install.py --list-backups

Touches only: CLAUDE.md, settings.json (only with --hooks), rules/ai-governance-
coding.md, skills/ponytail/, ai-governance/ inside the Claude config dir.
Never reads or copies authentication data. Installs no third-party software.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent
PAYLOAD = KIT / "payload"
MARK = "AI Governance Starter Kit"
BEGIN = "<!-- BEGIN AI-GOVERNANCE-STARTER-KIT (managed block; edit outside it) -->"
END = "<!-- END AI-GOVERNANCE-STARTER-KIT -->"
BLOCK_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)
HOOK_ID = "ai-governance/hooks/session-lifecycle-trigger.py"
SKILL_MARKER = ".ai-governance-kit"
NEVER_TOUCH = {".claude.json", ".credentials.json", "credentials.json", "auth.json"}


def claude_dir(arg):
    if arg:
        return Path(arg).expanduser().resolve()
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser().resolve() if env else Path.home() / ".claude"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def render(path, prefix):
    """Payload file bytes, with the default ~/.claude/ prefix adapted if needed."""
    data = path.read_bytes()
    if prefix != "~/.claude" and path.suffix in (".md", ".py"):
        data = data.decode("utf-8").replace("~/.claude/", prefix + "/").encode("utf-8")
    return data


def tree(srcs, prefix):
    """dict relpath -> bytes for a list of (source dir, dest subdir) pairs."""
    out = {}
    for src, sub in srcs:
        for p in sorted(src.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store":
                rel = (Path(sub) / p.relative_to(src)).as_posix()
                out[rel] = render(p, prefix)
    return out


def disk_tree(d):
    out = {}
    if d.is_dir() and not d.is_symlink():
        for p in sorted(d.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                out[p.relative_to(d).as_posix()] = p.read_bytes()
    return out


class Run:
    def __init__(self, cd, dry):
        self.cd, self.dry = cd, dry
        self.stamp = time.strftime("%Y%m%d-%H%M%S")
        self.bdir = cd / "ai-governance-kit-backups" / self.stamp
        n = 0
        while self.bdir.exists():
            n += 1
            self.bdir = cd / "ai-governance-kit-backups" / ("%s-%d" % (self.stamp, n))
        self.entries, self.made_dirs, self.warnings, self.changes = [], [], [], []

    def log(self, msg):
        print(("[dry-run] " if self.dry else "") + msg)

    def backup(self, path):
        assert path.name not in NEVER_TOUCH, "refusing to touch auth data: %s" % path
        entry = {"path": str(path), "backup": None}
        if path.exists() or path.is_symlink():
            dest = self.bdir / "files" / str(len(self.entries))
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.is_dir() and not path.is_symlink():
                shutil.copytree(path, dest, symlinks=True)
            else:
                shutil.copy2(path, dest, follow_symlinks=False)
            entry["backup"] = str(dest.relative_to(self.bdir))
        self.entries.append(entry)

    def mkdirs(self, d):
        missing = []
        while not d.exists():
            missing.append(d)
            d = d.parent
        for m in reversed(missing):
            m.mkdir()
            self.made_dirs.append(str(m))

    def write_file(self, path, data):
        self.backup(path)
        self.mkdirs(path.parent)
        tmp = path.with_name(path.name + ".kit-tmp")
        tmp.write_bytes(data)
        os.replace(str(tmp), str(path))

    def write_tree(self, d, files):
        self.backup(d)
        self.mkdirs(d.parent)
        tmp = d.with_name(d.name + ".kit-tmp")
        if tmp.exists():
            shutil.rmtree(tmp)
        for rel, data in files.items():
            f = tmp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
            if f.suffix in (".py", ".sh"):
                f.chmod(0o755)
        if d.exists():
            shutil.rmtree(d)
        os.replace(str(tmp), str(d))

    def finish(self, force=False):
        if (self.dry and not force) or not self.entries:
            return
        self.bdir.mkdir(parents=True, exist_ok=True)
        (self.bdir / "manifest.json").write_text(json.dumps(
            {"kit_version": (KIT / "VERSION").read_text().strip(), "entries": self.entries,
             "made_dirs": self.made_dirs}, indent=2))


# ---------------------------------------------------------------- components
def do_governance(r, prefix):
    want = tree([(PAYLOAD / "governance", ""), (PAYLOAD / "hooks", "hooks"),
                 (PAYLOAD / "templates", "templates")], prefix)
    want["VERSION"] = (KIT / "VERSION").read_bytes()
    d = r.cd / "ai-governance"
    if d.is_symlink():
        r.warnings.append("ai-governance/ is a symlink; left untouched")
        return
    if d.exists() and not (d / "GLOBAL-RULES.md").exists():
        r.warnings.append("ai-governance/ exists but is not this kit's; left untouched")
        return
    if disk_tree(d) == want:
        return r.log("ok      ai-governance/ up to date")
    r.log("%s ai-governance/ (%d files)" % ("update " if d.exists() else "create ", len(want)))
    r.changes.append("governance")
    if not r.dry:
        r.write_tree(d, want)


def do_rules(r, prefix):
    src = PAYLOAD / "rules" / "ai-governance-coding.md"
    dst = r.cd / "rules" / src.name
    data = render(src, prefix)
    if dst.exists():
        cur = dst.read_bytes()
        if cur == data:
            return r.log("ok      rules/%s up to date" % src.name)
        if MARK.encode() not in cur:
            r.warnings.append("rules/%s exists and is not this kit's; skipped" % src.name)
            return
    r.log("%s rules/%s" % ("update " if dst.exists() else "create ", src.name))
    r.changes.append("rules")
    if not r.dry:
        r.write_file(dst, data)


def do_skills(r, prefix):
    base = PAYLOAD / "skills"
    for sk in sorted(p for p in base.iterdir() if p.is_dir()):
        dst = r.cd / "skills" / sk.name
        want = tree([(sk, "")], prefix)
        want[SKILL_MARKER] = b"installed by AI Governance Starter Kit\n"
        if dst.exists() or dst.is_symlink():
            if dst.is_symlink() or not (dst / SKILL_MARKER).exists():
                r.warnings.append("skills/%s already exists (not from this kit); left untouched" % sk.name)
                continue
            if disk_tree(dst) == want:
                r.log("ok      skills/%s up to date" % sk.name)
                continue
        r.log("%s skills/%s" % ("update " if dst.exists() else "create ", sk.name))
        r.changes.append("skill:" + sk.name)
        if not r.dry:
            r.write_tree(dst, want)


def do_claude_md(r, prefix):
    path = r.cd / "CLAUDE.md"
    imp = "@%s/ai-governance/GLOBAL-RULES.md" % prefix
    block = "%s\n%s\n%s\n" % (BEGIN, imp, END)
    cur = path.read_text(encoding="utf-8") if path.exists() else ""
    foreign = [l for l in BLOCK_RE.sub("", cur).splitlines()
               if l.startswith("@") and l.strip().endswith("GLOBAL-RULES.md")]
    if foreign:
        r.warnings.append("CLAUDE.md already imports another GLOBAL-RULES.md (%s); both will load - "
                          "review for conflicting rules" % foreign[0].strip())
    if BLOCK_RE.search(cur):
        new = BLOCK_RE.sub("", cur)  # drop every copy, then re-add exactly one in place
        first = BLOCK_RE.search(cur).start()
        new = new[:first] + block + new[first:]
    else:
        sep = "" if not cur else ("\n" if cur.endswith("\n") else "\n\n")
        new = cur + sep + block
    if new == cur:
        return r.log("ok      CLAUDE.md managed block up to date")
    r.log("%s CLAUDE.md (managed block; existing content preserved)" % ("update " if cur else "create "))
    r.changes.append("claude.md")
    if not r.dry:
        r.write_file(path, new.encode("utf-8"))


def hook_command(r):
    script = (r.cd / "ai-governance" / "hooks" / "session-lifecycle-trigger.py").as_posix()
    if platform.system() == "Windows":
        # Hooks run in Git Bash or PowerShell: a bare command name works in both (a quoted
        # executable at the start does not work in PowerShell).
        exe = "python" if shutil.which("python") else "py -3"
        return '%s "%s"' % (exe, script)
    return 'python3 "%s"' % script


def do_hooks(r):
    path = r.cd / "settings.json"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        assert isinstance(cfg, dict)
    except Exception:
        r.warnings.append("settings.json is not valid JSON; hook NOT registered (file untouched)")
        return
    import copy
    new = copy.deepcopy(cfg)
    groups = new.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
    cmd, found = hook_command(r), False
    for g in groups:
        for h in g.get("hooks", []):
            if HOOK_ID in h.get("command", "").replace("\\", "/"):
                if found:
                    h["command"] = None  # duplicate, removed below
                else:
                    h["command"], h["timeout"], found = cmd, 5, True
    for g in groups:
        g["hooks"] = [h for h in g.get("hooks", []) if h.get("command") is not None]
    new["hooks"]["UserPromptSubmit"] = [g for g in groups if g.get("hooks")]
    if not found:
        new["hooks"]["UserPromptSubmit"].append(
            {"hooks": [{"type": "command", "command": cmd, "timeout": 5}]})
    if new == cfg:
        return r.log("ok      settings.json hook already registered")
    r.log("%s settings.json (adds 1 UserPromptSubmit hook; other settings preserved)"
          % ("update " if path.exists() else "create "))
    r.changes.append("hooks")
    if not r.dry:
        r.write_file(path, (json.dumps(new, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


# ---------------------------------------------------------------- rollback
def backups(cd):
    b = cd / "ai-governance-kit-backups"
    return sorted(p for p in b.iterdir() if (p / "manifest.json").exists()) if b.is_dir() else []


def rollback(cd, which, dry):
    bl = backups(cd)
    if not bl:
        print("No kit backups found in %s" % (cd / "ai-governance-kit-backups"))
        return 1
    target = next((b for b in bl if b.name == which), None) if which else bl[-1]
    if not target:
        print("Backup %r not found. Available: %s" % (which, ", ".join(b.name for b in bl)))
        return 1
    m = json.loads((target / "manifest.json").read_text())
    print("%sRolling back %s" % ("[dry-run] " if dry else "", target.name))
    for e in reversed(m["entries"]):
        p = Path(e["path"])
        print("%s  %s  %s" % ("[dry-run] " if dry else "", "restore" if e["backup"] else "remove ", p))
        if dry:
            continue
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)
        elif p.exists() or p.is_symlink():
            p.unlink()
        if e["backup"]:
            src = target / e["backup"]
            if src.is_dir():
                shutil.copytree(src, p, symlinks=True)
            else:
                shutil.copy2(src, p, follow_symlinks=False)
    if not dry:
        for d in reversed(m["made_dirs"]):
            try:
                Path(d).rmdir()
            except OSError:
                pass
        shutil.move(str(target), str(target) + ".rolled-back")
        print("Done. Backup kept as %s.rolled-back" % target.name)
    return 0


# ---------------------------------------------------------------- main
def preflight():
    print("OS: %s %s | Python %s" % (platform.system(), platform.release(), platform.python_version()))
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required")
        return False
    for tool, need in (("claude", "optional (the VS Code extension bundles Claude Code)"),
                       ("git", "recommended"), ("code", "optional")):
        print("  %-7s %s" % (tool, "found" if shutil.which(tool) else "not on PATH - " + need))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="show the plan, write nothing")
    ap.add_argument("--hooks", action="store_true", help="register the optional START/END hook")
    ap.add_argument("--no-skills", action="store_true", help="do not install skills")
    ap.add_argument("--claude-dir", help="Claude config dir (default: $CLAUDE_CONFIG_DIR or ~/.claude)")
    ap.add_argument("--rollback", nargs="?", const="", metavar="BACKUP_ID",
                    help="restore the state before the last (or given) change")
    ap.add_argument("--list-backups", action="store_true")
    a = ap.parse_args()
    cd = claude_dir(a.claude_dir)

    if a.list_backups:
        for b in backups(cd):
            print(b.name)
        return 0
    if a.rollback is not None:
        return rollback(cd, a.rollback or None, a.dry_run)
    if not preflight():
        return 1
    print("Claude config dir: %s%s\n" % (cd, "" if cd.exists() else "  (will be created)"))
    prefix = cd.as_posix()  # absolute, generated on this machine (verified import form)
    r = Run(cd, a.dry_run)
    try:
        do_governance(r, prefix)
        do_rules(r, prefix)
        if not a.no_skills:
            do_skills(r, prefix)
        do_claude_md(r, prefix)
        if a.hooks:
            do_hooks(r)
        else:
            r.log("skip    hook (optional; add --hooks to register START/END trigger)")
    except Exception as e:  # recoverable failure: undo this run, leave config as it was
        print("\nERROR: installation failed (%s: %s)" % (type(e).__name__, e))
        r.finish(force=True)
        if r.entries:
            print("Undoing the partial installation...")
            rc = rollback(cd, r.bdir.name, False)
            print("Configuration restored." if rc == 0 else "Automatic undo failed; run: python3 install.py --rollback")
        for t in list(cd.rglob("*.kit-tmp")):
            shutil.rmtree(t) if t.is_dir() else t.unlink()
        return 2
    r.finish()
    for w in r.warnings:
        print("WARNING: " + w)
    print()
    if not r.changes:
        print("Nothing to change - already up to date.")
    elif a.dry_run:
        print("Dry run only. Nothing was written. Re-run without --dry-run to apply.")
    else:
        print("Installed. Backup of replaced files: %s" % r.bdir)
        print("Rollback: python3 install.py --rollback   (see docs/ROLLBACK.md)")
        print("Next: restart VS Code / start a new Claude Code session, then run: python3 verify.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
