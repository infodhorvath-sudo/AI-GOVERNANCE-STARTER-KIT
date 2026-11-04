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


def import_ref(cd):
    """(prefix, @import path) for the config dir.

    Under the home folder the documented `~/` form is used: observed to load with spaces and Unicode in
    the path, and it keeps machine-specific paths out of CLAUDE.md. Elsewhere an absolute path is used with
    spaces backslash-escaped (an unescaped space silently breaks the @import)."""
    for home, c in ((Path.home(), cd), (Path.home().resolve(), cd.resolve())):
        try:
            rel = c.relative_to(home).as_posix()
            return "~/" + rel, "~/%s/ai-governance/GLOBAL-RULES.md" % rel
        except ValueError:
            pass
    ab = cd.as_posix()
    return ab, (ab + "/ai-governance/GLOBAL-RULES.md").replace(" ", "\\ ")


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


STATE_REL = "ai-governance/.kit-state.json"


def load_state(cd):
    try:
        return json.loads((cd / STATE_REL).read_text(encoding="utf-8"))["files"]
    except Exception:
        return None


class Run:
    def __init__(self, cd, dry, force=False):
        self.cd, self.dry, self.force = cd, dry, force
        self.state_old = load_state(cd)  # None = no record (pre-1.0.1 install or fresh)
        self.state_new = {}
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
        self.entries[-1]["after"] = sha(data)  # lets rollback detect later edits by the user

    def finish(self, force=False):
        if (self.dry and not force) or not self.entries:
            return
        self.bdir.mkdir(parents=True, exist_ok=True)
        (self.bdir / "manifest.json").write_text(json.dumps(
            {"kit_version": (KIT / "VERSION").read_text().strip(), "entries": self.entries,
             "made_dirs": self.made_dirs}, indent=2))


# ---------------------------------------------------------------- components
def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".kit-tmp")
    tmp.write_bytes(data)
    if path.suffix in (".py", ".sh"):
        tmp.chmod(0o755)
    os.replace(str(tmp), str(path))


def sync(r, label, base, want, own_dir, backup_target):
    """Bring kit-owned files under `base` to `want` ({rel: bytes}) without clobbering user edits.

    A file is replaced when it is absent, identical, recorded as installed by the kit and unchanged since,
    or when there is no record (installed by a release that kept none; it is backed up). A file changed by the
    user since install is KEPT and reported unless --force. Files of the kit's earlier version that no longer
    exist are removed only if unmodified. Files the user added are never touched."""
    relbase = base.relative_to(r.cd).as_posix()
    old = r.state_old or {}
    write, remove, kept = {}, [], []
    for rel, data in want.items():
        key = "%s/%s" % (relbase, rel)
        f = base / rel
        cur = f.read_bytes() if f.is_file() else None
        if cur == data:
            r.state_new[key] = sha(data)
        elif cur is None or key not in old or sha(cur) == old[key] or r.force:
            write[rel] = data
            r.state_new[key] = sha(data)
        else:
            kept.append(rel)
            r.state_new[key] = old[key]
    if own_dir:
        for key, h in old.items():
            if key.startswith(relbase + "/") and key[len(relbase) + 1:] not in want:
                f = r.cd / key
                if f.is_file() and sha(f.read_bytes()) == h:
                    remove.append(f)
    for rel in kept:
        r.warnings.append(
            "%s/%s was modified by you since install; KEPT (this release ships a different version: "
            "payload/ in the kit folder). Merge by hand or re-run with --force to replace it (backup kept)."
            % (relbase, rel))
    if not write and not remove:
        r.log("ok      %s up to date%s" % (label, " (%d customized file(s) kept)" % len(kept) if kept else ""))
        return
    existed = base.exists()
    r.log("%s %s (%d file(s) written%s%s)" % ("update " if existed else "create ", label, len(write),
          ", %d removed" % len(remove) if remove else "", ", %d customized kept" % len(kept) if kept else ""))
    r.changes.append(label)
    if not r.dry:
        r.backup(backup_target)
        r.mkdirs(base)
        for rel, data in write.items():
            atomic_write(base / rel, data)
        for f in remove:
            f.unlink()


def do_governance(r, prefix):
    want = tree([(PAYLOAD / "governance", ""), (PAYLOAD / "hooks", "hooks"),
                 (PAYLOAD / "templates", "templates")], prefix)
    want["VERSION"] = (KIT / "VERSION").read_bytes()
    d = r.cd / "ai-governance"
    if d.is_symlink():
        r.warnings.append("ai-governance/ is a symlink; left untouched")
        return False
    if d.exists() and not (d / "GLOBAL-RULES.md").exists():
        r.warnings.append("ai-governance/ exists but is not this kit's; left untouched")
        return False
    sync(r, "ai-governance/", d, want, True, d)
    return True


def do_rules(r, prefix):
    src = PAYLOAD / "rules" / "ai-governance-coding.md"
    dst = r.cd / "rules" / src.name
    if dst.exists():
        key = "rules/" + src.name
        if key not in (r.state_old or {}) and MARK.encode() not in dst.read_bytes():
            r.warnings.append("rules/%s exists and is not this kit's; skipped" % src.name)
            return
    sync(r, "rules/" + src.name, dst.parent, {src.name: render(src, prefix)}, False, dst)


def do_skills(r, prefix):
    base = PAYLOAD / "skills"
    for sk in sorted(p for p in base.iterdir() if p.is_dir()):
        dst = r.cd / "skills" / sk.name
        want = tree([(sk, "")], prefix)
        want[SKILL_MARKER] = b"installed by AI Governance Starter Kit\n"
        if dst.is_symlink() or (dst.exists() and not (dst / SKILL_MARKER).exists()):
            r.warnings.append("skills/%s already exists (not from this kit); left untouched" % sk.name)
            continue
        sync(r, "skills/" + sk.name, dst, want, True, dst)


def write_state(r):
    new = dict(r.state_old or {})
    new.update(r.state_new)
    data = (json.dumps({"kit_version": (KIT / "VERSION").read_text().strip(), "files": new},
                       indent=1, sort_keys=True) + "\n").encode("utf-8")
    path = r.cd / STATE_REL
    if path.exists() and path.read_bytes() == data:
        return
    r.changes.append("state")
    if not r.dry:
        r.write_file(path, data)


def do_claude_md(r, imp_path):
    path = r.cd / "CLAUDE.md"
    imp = "@" + imp_path
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
    r.log("create  CLAUDE.md (managed block)" if not cur else
          "update  CLAUDE.md (managed block %s; your content preserved)" % ("refreshed" if BLOCK_RE.search(cur) else "added"))
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
    return sorted(p for p in b.iterdir() if (p / "manifest.json").exists() and not p.name.endswith(".rolled-back")) if b.is_dir() else []


def strip_kit(p):
    """The file was edited after install: remove only what the kit added. Returns a description or None."""
    try:
        if p.name == "CLAUDE.md":
            new = re.sub(r"\n{3,}", "\n\n", BLOCK_RE.sub("", p.read_text(encoding="utf-8")))
            p.write_text(new.rstrip("\n") + "\n" if new.strip() else "", encoding="utf-8")
            return "removed only the kit's managed block (your later edits kept)"
        if p.name == "settings.json":
            cfg = json.loads(p.read_text(encoding="utf-8"))
            ups = cfg.get("hooks", {}).get("UserPromptSubmit", [])
            for g in ups:
                g["hooks"] = [h for h in g.get("hooks", []) if HOOK_ID not in h.get("command", "").replace("\\", "/")]
            cfg["hooks"]["UserPromptSubmit"] = [g for g in ups if g["hooks"]]
            if not cfg["hooks"]["UserPromptSubmit"]:
                del cfg["hooks"]["UserPromptSubmit"]
            if not cfg["hooks"]:
                del cfg["hooks"]
            p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return "removed only the kit's hook entry (your later edits kept)"
    except Exception:
        pass
    return None


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
        edited = ("after" in e and p.is_file() and sha(p.read_bytes()) != e["after"]
                  and p.name in ("CLAUDE.md", "settings.json"))
        print("%s  %s  %s%s" % ("[dry-run] " if dry else "", "edit   " if edited else ("restore" if e["backup"] else "remove "), p,
                              "  (changed since install: only the kit's part is removed)" if edited else ""))
        if dry:
            continue
        if edited:
            msg = strip_kit(p)
            if msg:
                print("            " + msg)
                continue
            print("            could not edit safely; left untouched, see %s" % (target / (e["backup"] or "")))
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
    ap.add_argument("--force", action="store_true", help="also replace kit files you have modified (backed up first)")
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
    prefix, imp_path = import_ref(cd)
    r = Run(cd, a.dry_run, a.force)
    try:
        gov_ok = do_governance(r, prefix)
        do_rules(r, prefix)
        if not a.no_skills:
            do_skills(r, prefix)
        if gov_ok:
            write_state(r)
        do_claude_md(r, imp_path)
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
        print("Installed. Undo record and backups of anything replaced: %s" % r.bdir)
        print("Rollback: python3 install.py --rollback   (see docs/ROLLBACK.md)")
        print("Next: restart VS Code / start a new Claude Code session, then run: python3 verify.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
