#!/usr/bin/env python3
"""Verification for the AI Governance Starter Kit (Python 3.8+, stdlib only).

  python3 verify.py                 package integrity + isolated sandbox install tests
                                    + status of the REAL target config + runtime guidance
  python3 verify.py --live          also ask Claude (3 tiny Haiku requests, your own login)
  python3 verify.py --no-sandbox    skip the sandbox scenarios (faster)
  python3 verify.py --claude-dir D  check another config dir (default ~/.claude / $CLAUDE_CONFIG_DIR)

Four independent levels, each reported separately:
  1. PACKAGE      is the kit itself healthy (no secrets, complete, no import cycles)?
  2. SANDBOX      does install / repeat / rollback / failure recovery work in a throwaway dir?
  3. TARGET       is the kit installed in the target config, and correctly?
  4. RUNTIME      does Claude Code really load the rules? (needs --live or a manual check)

Statuses: PASS, FAIL, NOT INSTALLED, NOT TESTED, MANUAL VERIFICATION REQUIRED.
Exit code: 1 if any FAIL; else 2 if the target is NOT INSTALLED; else 0.
A kit that is not installed is never reported as FAIL.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent
PY = sys.executable
VERSION = (KIT / "VERSION").read_text().strip()
CANARY = "AIGOV-KIT-%s-LOADED" % VERSION
STATUS = []


def report(status, msg):
    STATUS.append(status)
    print("  %-30s %s" % (status, msg))
    return status == "PASS"


def check(ok, msg):
    return report("PASS" if ok else "FAIL", msg)


def claude_dir(arg):
    if arg:
        return Path(arg).expanduser().resolve()
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser().resolve() if env else Path.home() / ".claude"


def snapshot(root, skip=("ai-governance-kit-backups",)):
    out = {}
    root = Path(root)
    for p in sorted(root.rglob("*")):
        if not any(s in p.parts for s in skip):
            out[p.relative_to(root).as_posix()] = (
                hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<dir>")
    return out


def run(args, **kw):
    return subprocess.run([PY] + [str(a) for a in args], capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- 1. package
def package():
    print("\n[1] PACKAGE INTEGRITY")
    bad = [r"sk-ant-[A-Za-z0-9_-]{10,}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}",
           r"xox[bp]-[A-Za-z0-9-]{10,}", r"-----BEGIN [A-Z ]*PRIVATE KEY", r"/Users/[A-Za-z]",
           r"C:\\Users\\", r"/home/[a-z]", r"@gmail\.com"]
    rx = re.compile("|".join(bad))
    hits, files = [], [p for p in KIT.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                       and ".git" not in p.parts and p.name != ".DS_Store"]
    for p in files:
        if p.name == "verify.py":
            continue
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if rx.search(line):
                    hits.append("%s:%d" % (p.relative_to(KIT), i))
        except UnicodeDecodeError:
            pass
    check(not hits, "no secrets / personal data / absolute user paths %s" % (hits[:5] or ""))
    forbidden = {".claude.json", ".credentials.json", "settings.json", "history.jsonl", ".env"}
    check(not [p for p in files if p.name in forbidden], "no auth / settings / history files shipped")
    need = ["install.py", "verify.py", "README.md", "VERSION", "LICENSE", "THIRD-PARTY-NOTICES.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "docs/ROLLBACK.md", "docs/ACTIVATION.md",
            "docs/VERIFY-IN-VSCODE.md", "payload/governance/GLOBAL-RULES.md",
            "payload/governance/bootstrap-project.py", "payload/hooks/session-lifecycle-trigger.py",
            "payload/rules/ai-governance-coding.md", "payload/skills/ponytail/SKILL.md",
            "payload/skills/ponytail/LICENSE", "payload/templates/project/CLAUDE.md",
            "payload/templates/project/.ai/STATE.md", "payload/templates/project/.ai/SESSION-LOG.md"]
    need += ["payload/governance/modules/%s.md" % m for m in ("AUTONOMY-GIT-SAFETY", "LIFECYCLE-CONTEXT", "COST-REVIEW-TOOLS")]
    missing = [n for n in need if not (KIT / n).exists()]
    check(not missing, "all required files present %s" % (missing or ""))
    bad_py = []
    for p in KIT.rglob("*.py"):
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            bad_py.append(p.name)
    check(not bad_py, "all Python scripts parse %s" % (bad_py or ""))
    # imports: none inside payload docs (modules are referenced as plain paths) => no cycles, no broken refs
    crlf = [p.relative_to(KIT).as_posix() for p in files if p.suffix != ".png" and b"\r\n" in p.read_bytes()]
    check(not crlf, "no CRLF line endings (a CRLF checkout breaks manifest hashes and shebangs) %s" % (crlf[:3] or ""))
    ga = KIT / ".gitattributes"
    if (KIT / ".git").exists() or ga.exists():
        check(ga.exists() and "eol=lf" in ga.read_text() and "png binary" in ga.read_text(), ".gitattributes forces LF for text and marks PNG binary")
    broken = []
    for md in ("README.md", "docs/INSTALLATION-GUIDE.md"):
        base = (KIT / md).parent
        for ref in re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", (KIT / md).read_text(encoding="utf-8")):
            if not ref.startswith("http") and not (base / ref).exists():
                broken.append("%s -> %s" % (md, ref))
    check(not broken, "every image referenced by README and the installation guide exists %s" % (broken[:3] or ""))
    try:
        rd = (KIT / "README.md").read_text(encoding="utf-8")
        gd = (KIT / "docs/INSTALL-WITH-CLAUDE.md").read_text(encoding="utf-8")
        pr = re.search(r"## Install with Claude Code.*?```text\n(.*?)\n```", rd, re.S).group(1)
        pg = re.search(r"## The prompt.*?```text\n(.*?)\n```", gd, re.S).group(1)
        ok = (pr == pg and "https://github.com/infodhorvath-sudo/AI-GOVERNANCE-STARTER-KIT.git" in pr
              and not re.search(r"\d+\.\d+\.\d+|curl|(?<![-\w])sudo(?![-\w])|\| *(ba)?sh", pr))
    except (AttributeError, OSError):
        ok = False
    check(ok, "Install-with-Claude prompt: identical in README and guide, official URL, no version number, no curl/sudo/pipe-to-shell")
    imports = [(p.name, l) for p in (KIT / "payload").rglob("*.md") for l in p.read_text(encoding="utf-8").splitlines()
               if l.startswith("@")]
    check(not imports, "payload files contain no @imports (no cycles / broken imports possible) %s" % (imports[:2] or ""))
    gr = (KIT / "payload/governance/GLOBAL-RULES.md").read_text(encoding="utf-8")
    check(("Kit-Version: " + VERSION) in gr and CANARY in gr, "GLOBAL-RULES.md carries Kit-Version %s and canary" % VERSION)
    sk = (KIT / "payload/skills/ponytail/SKILL.md").read_text(encoding="utf-8")
    check(sk.startswith("---\n") and re.search(r"^name:\s*ponytail\s*$", sk, re.M) and re.search(r"^description:", sk, re.M),
          "ponytail SKILL.md: frontmatter starts on line 1, has name + description")
    man = KIT / "RELEASE-MANIFEST.json"
    if man.exists():
        m = json.loads(man.read_text())
        diff = [f for f, h in m["files"].items()
                if not (KIT / f).exists() or hashlib.sha256((KIT / f).read_bytes()).hexdigest() != h]
        extra = [p.relative_to(KIT).as_posix() for p in files if p.name != "RELEASE-MANIFEST.json"
                 and p.relative_to(KIT).as_posix() not in m["files"]]
        check(not diff and not extra, "RELEASE-MANIFEST checksums match (changed/missing: %s, unlisted: %s)" % (diff[:3], extra[:3]))
    else:
        report("NOT TESTED", "RELEASE-MANIFEST.json absent (only present in release archives)")


# ---------------------------------------------------------------- shared installed-state check
def installed_state(cd, expect_hook=None, home=None):
    imp_re = re.compile(r"^@((?:\\ |\S)+)", re.M)
    md = cd / "CLAUDE.md"
    text = md.read_text(encoding="utf-8") if md.exists() else ""
    check(text.count("BEGIN AI-GOVERNANCE-STARTER-KIT") == 1 and text.count("END AI-GOVERNANCE-STARTER-KIT") == 1,
          "CLAUDE.md contains exactly one managed block")
    imports = imp_re.findall(text)
    kit_imp = [i for i in imports if i.endswith("ai-governance/GLOBAL-RULES.md")]
    check(len(kit_imp) == 1, "exactly one kit @import in CLAUDE.md")
    h = Path(home) if home else Path.home()
    res = lambda i: (h / i[2:]) if i.startswith("~/") else Path(i.replace("\\ ", " "))
    unresolved = [i for i in imports if not res(i).exists()]
    check(not unresolved, "every @import in CLAUDE.md resolves to an existing file %s" % (unresolved or ""))
    gr = cd / "ai-governance" / "GLOBAL-RULES.md"
    check(gr.exists() and CANARY in gr.read_text(encoding="utf-8"), "GLOBAL-RULES.md installed (canary %s)" % CANARY)
    check(all((cd / "ai-governance" / "modules" / m).exists()
              for m in ("AUTONOMY-GIT-SAFETY.md", "LIFECYCLE-CONTEXT.md", "COST-REVIEW-TOOLS.md")), "3 on-demand modules present")
    check((cd / "rules" / "ai-governance-coding.md").exists(), "rules/ai-governance-coding.md present")
    sk = cd / "skills" / "ponytail" / "SKILL.md"
    check(sk.exists() and sk.read_text(encoding="utf-8").startswith("---\n") and (cd / "skills/ponytail/LICENSE").exists(),
          "skill ponytail + LICENSE present, frontmatter valid")
    st = cd / "settings.json"
    cfg = {}
    if st.exists():
        try:
            cfg = json.loads(st.read_text(encoding="utf-8"))
        except ValueError:
            check(False, "settings.json is valid JSON")
    cmds = [h.get("command", "") for g in cfg.get("hooks", {}).get("UserPromptSubmit", [])
            for h in g.get("hooks", []) if "ai-governance/hooks/session-lifecycle-trigger.py" in h.get("command", "").replace("\\", "/")]
    if expect_hook is True or (expect_hook is None and cmds):
        check(len(cmds) == 1, "START/END hook registered exactly once")
        script = cd / "ai-governance" / "hooks" / "session-lifecycle-trigger.py"
        r1 = subprocess.run([PY, str(script)], input='{"prompt":"start"}', capture_output=True, text=True)
        r2 = subprocess.run([PY, str(script)], input='{"prompt":"please start the server"}', capture_output=True, text=True)
        check(r1.returncode == 0 and "SESSION_LIFECYCLE_START_TRIGGER" in r1.stdout, "hook fires on exact 'start'")
        check(r2.returncode == 0 and r2.stdout.strip() == "", "hook silent for ordinary sentences")
    else:
        print("  %-30s optional START/END hook (install.py --hooks)" % "info")


# ---------------------------------------------------------------- 2. sandbox scenarios
def seed_config(cfg):
    (cfg / "rules").mkdir(parents=True)
    (cfg / "skills" / "mine").mkdir(parents=True)
    (cfg / "CLAUDE.md").write_text("# My own rules\nBe nice.\n")
    (cfg / "settings.json").write_text(json.dumps({"model": "x", "hooks": {"Stop": [
        {"hooks": [{"type": "command", "command": "echo hi"}]}]}}, indent=2))
    (cfg / "rules" / "mine.md").write_text("my rule\n")
    (cfg / "skills" / "mine" / "SKILL.md").write_text("---\nname: mine\n---\n")
    (cfg / ".claude.json").write_text('{"oauth":"FAKE-AUTH-DATA"}')


def sandbox():
    print("\n[2] ISOLATED INSTALLATION TESTS (throwaway sandbox; your real config is never touched)")
    tmp = Path(tempfile.mkdtemp(prefix="kit-sandbox-"))
    try:
        inst = lambda cfg, *a: run([KIT / "install.py", "--claude-dir", cfg] + list(a))
        boot = lambda cfg, d, *a: run([cfg / "ai-governance" / "bootstrap-project.py", d] + list(a))

        print(" A. fresh environment (no Claude config at all)")
        fresh = tmp / "fresh" / ".claude"
        r = inst(fresh, "--hooks")
        check(r.returncode == 0 and fresh.exists(), "installer succeeds and creates the config dir")
        installed_state(fresh, expect_hook=True)
        r = inst(fresh, "--rollback")
        check(r.returncode == 0 and not (fresh / "ai-governance").exists() and not (fresh / "CLAUDE.md").exists()
              and not (fresh / "skills").exists() and not (fresh / "rules").exists(),
              "rollback of a fresh install leaves no kit files or directories")

        print(" B. existing developer configuration")
        cfg = tmp / "cfg"
        seed_config(cfg)
        (cfg / "skills" / "ponytail").mkdir()
        (cfg / "skills" / "ponytail" / "SKILL.md").write_text("---\nname: ponytail\n---\nMY OWN\n")
        (cfg / "rules" / "ai-governance-coding.md").write_text("somebody else's rule\n")
        orig = snapshot(cfg)
        r = inst(cfg, "--hooks", "--dry-run")
        check(r.returncode == 0 and snapshot(cfg) == orig, "dry-run writes nothing")
        r = inst(cfg, "--hooks")
        after = snapshot(cfg)
        check(r.returncode == 0, "install succeeds")
        check("skills/ponytail" in r.stdout + "" and r.stdout.count("WARNING") >= 2, "conflicts (same-name skill, same-name rule) are reported as warnings")
        check((cfg / "skills/ponytail/SKILL.md").read_text().endswith("MY OWN\n") and
              (cfg / "rules/ai-governance-coding.md").read_text() == "somebody else's rule\n",
              "conflicting user skill and rule NOT overwritten")
        check((cfg / "CLAUDE.md").read_text().startswith("# My own rules\nBe nice.\n"), "existing CLAUDE.md content preserved")
        s = json.loads((cfg / "settings.json").read_text())
        check(s["model"] == "x" and s["hooks"]["Stop"][0]["hooks"][0]["command"] == "echo hi", "existing settings and hooks preserved")
        check(after[".claude.json"] == orig[".claude.json"] and not any(
            ".claude.json" in str(p) for p in (cfg / "ai-governance-kit-backups").rglob("*")), "auth file untouched, never backed up")

        print(" C. repeated installation")
        r = inst(cfg, "--hooks")
        check("Nothing to change" in r.stdout and snapshot(cfg) == after, "second install changes nothing (no duplicates)")
        check(len(list((cfg / "ai-governance-kit-backups").glob("*/manifest.json"))) == 1, "no extra backup created")
        t = (cfg / "CLAUDE.md").read_text()
        check(t.count("BEGIN AI-GOVERNANCE-STARTER-KIT") == 1, "exactly one managed block after repeat")

        print(" E. existing project with its own instructions")
        proj = tmp / "existing-project"
        proj.mkdir()
        (proj / "CLAUDE.md").write_text("# existing project\nUse tabs.\n")
        (proj / "app.py").write_text("print(1)\n")
        po = snapshot(proj)
        inst(cfg, "--hooks")
        check(snapshot(proj) == po, "install leaves the existing project untouched")
        boot(cfg, proj)
        now = snapshot(proj)
        check(now["CLAUDE.md"] == po["CLAUDE.md"] and now["app.py"] == po["app.py"],
              "bootstrap never overwrites the project's CLAUDE.md or code")

        print(" F. new project")
        np = tmp / "new-project"
        b = boot(cfg, np, "--name", "Demo")
        check(b.returncode == 0 and all((np / f).exists() for f in ("CLAUDE.md", ".ai/STATE.md", ".ai/SESSION-LOG.md")),
              "optional bootstrap creates CLAUDE.md + .ai/ files in an empty project")
        c = (np / "CLAUDE.md").read_text()
        check("{{" not in c and "Demo" in c and "Kit-Version" not in c, "project CLAUDE.md is filled in and does not duplicate global rules")
        check(not (tmp / "new-project" / ".claude").exists(), "global rules need no per-project files (nothing global copied into the project)")
        h = boot(cfg, Path.home())
        check(h.returncode == 1 and "Refusing" in h.stdout, "bootstrap refuses your home directory with a clear message")

        print(" D. rollback")
        r = inst(cfg, "--rollback", "--dry-run")
        check(r.returncode == 0 and snapshot(cfg) != orig, "rollback --dry-run changes nothing")
        r = inst(cfg, "--rollback")
        check(r.returncode == 0 and snapshot(cfg) == orig, "rollback restores the exact original configuration")

        print(" G. failure recovery")
        bad = tmp / "bad"
        seed_config(bad)
        shutil.rmtree(bad / "rules")
        (bad / "rules").write_text("I am a file, not a directory\n")  # forces a mid-install failure
        bo = snapshot(bad)
        r = inst(bad, "--hooks")
        check(r.returncode == 2 and "ERROR" in r.stdout, "mid-install failure is reported clearly (exit 2)")
        check(snapshot(bad) == bo and not list(bad.rglob("*.kit-tmp")), "partial work undone automatically; config identical to before")
        badj = tmp / "badjson"
        seed_config(badj)
        (badj / "settings.json").write_text("{ not json")
        bj = (badj / "settings.json").read_bytes()
        r = inst(badj, "--hooks")
        check(r.returncode == 0 and (badj / "settings.json").read_bytes() == bj and "not valid JSON" in r.stdout,
              "invalid settings.json is left byte-identical with a warning")

        print(" I. update over an earlier installation")
        up = tmp / "upd"
        seed_config(up)
        pristine = snapshot(up)
        inst(up, "--hooks")
        gr = up / "ai-governance" / "GLOBAL-RULES.md"
        gr.write_text("Kit-Version: 0.9 (older)\n")
        (up / "ai-governance" / "modules" / "COST-REVIEW-TOOLS.md").unlink()
        (up / "rules" / "ai-governance-coding.md").write_text("# old AI Governance Starter Kit rule\n")
        with open(up / "CLAUDE.md", "a") as f:
            f.write("\nMy later personal rule.\n")
        stp = up / "ai-governance" / ".kit-state.json"  # what an older release would have recorded
        st = json.loads(stp.read_text())
        for k in ("ai-governance/GLOBAL-RULES.md", "rules/ai-governance-coding.md"):
            st["files"][k] = hashlib.sha256((up / k).read_bytes()).hexdigest()
        stp.write_text(json.dumps(st, indent=1, sort_keys=True) + "\n")
        old = snapshot(up)
        r = inst(up, "--hooks")
        t = (up / "CLAUDE.md").read_text()
        check(r.returncode == 0 and CANARY in gr.read_text() and (up / "ai-governance/modules/COST-REVIEW-TOOLS.md").exists(),
              "update replaces outdated kit-owned files")
        check("My later personal rule." in t and t.startswith("# My own rules") and t.count("BEGIN AI-GOVERNANCE-STARTER-KIT") == 1,
              "update keeps the user's own CLAUDE.md content and does not duplicate the import")
        check(len(list((up / "ai-governance-kit-backups").glob("*/manifest.json"))) == 2, "update made a new backup of what it replaced")
        r = inst(up, "--rollback")
        check(r.returncode == 0 and snapshot(up) == old, "rollback of the update restores the previous installation exactly")
        r = inst(up, "--rollback")
        now = snapshot(up)
        t = (up / "CLAUDE.md").read_text()
        check(r.returncode == 0 and {k: v for k, v in now.items() if k != "CLAUDE.md"} == {k: v for k, v in pristine.items() if k != "CLAUDE.md"}
              and t.startswith("# My own rules\nBe nice.\n") and "My later personal rule." in t and "AI-GOVERNANCE-STARTER-KIT" not in t,
              "a second rollback walks back to the state before the kit (full uninstall; your later CLAUDE.md line is kept)")

        print(" J. user customization of kit-owned files")
        cu = tmp / "custom"
        seed_config(cu)
        inst(cu)
        gr = cu / "ai-governance" / "GLOBAL-RULES.md"
        mine = gr.read_text() + "\nMY OWN CUSTOM RULE\n"
        gr.write_text(mine)
        (cu / "ai-governance" / "my-notes.md").write_text("my extra file\n")
        before = snapshot(cu)
        r = inst(cu)
        check(r.returncode == 0 and gr.read_text() == mine and "modified by you" in r.stdout,
              "customized kit file is KEPT and the conflict is reported (not silently overwritten)")
        check((cu / "ai-governance" / "my-notes.md").exists(), "files the user added inside kit folders are never removed")
        r = inst(cu, "--force")
        check(r.returncode == 0 and "MY OWN CUSTOM RULE" not in gr.read_text(), "--force replaces the customized file")
        r = inst(cu, "--rollback")
        check(r.returncode == 0 and gr.read_text() == mine, "rollback after --force restores the customized file (it was backed up)")
        (cu / "ai-governance" / ".kit-state.json").unlink()
        gr.write_text("legacy tampered\n")
        r = inst(cu)
        check(r.returncode == 0 and CANARY in gr.read_text(), "install without an install record (pre-1.0.1 install) replaces files, with a backup")

        print(" N. rollback after the user edited files since install")
        ed = tmp / "edited"
        seed_config(ed)
        before = snapshot(ed)
        inst(ed, "--hooks")
        with open(ed / "CLAUDE.md", "a") as f:
            f.write("\nEdited after install.\n")
        c = json.loads((ed / "settings.json").read_text())
        c["theme"] = "dark-later"
        (ed / "settings.json").write_text(json.dumps(c, indent=2))
        r = inst(ed, "--rollback")
        t = (ed / "CLAUDE.md").read_text()
        c = json.loads((ed / "settings.json").read_text())
        check(r.returncode == 0 and "Edited after install." in t and "AI-GOVERNANCE-STARTER-KIT" not in t and t.startswith("# My own rules"),
              "rollback keeps your later CLAUDE.md edits and removes only the kit's block")
        check(c.get("theme") == "dark-later" and c["model"] == "x" and c["hooks"]["Stop"][0]["hooks"][0]["command"] == "echo hi"
              and "UserPromptSubmit" not in c["hooks"], "rollback keeps your later settings.json edits and removes only the kit's hook")
        check(not (ed / "ai-governance").exists() and not (ed / "skills" / "ponytail").exists(), "kit-owned folders are removed")

        print(" K. unusual paths (spaces, Unicode)")
        for name in ("home with space", "h\u00f3me-\u65e5\u672c-\u0434\u043e\u043c"):
            hm = tmp / name
            hm.mkdir()
            env = dict(os.environ, HOME=str(hm), USERPROFILE=str(hm))
            env.pop("CLAUDE_CONFIG_DIR", None)
            r = subprocess.run([PY, str(KIT / "install.py"), "--hooks"], capture_output=True, text=True, env=env)
            md = (hm / ".claude" / "CLAUDE.md").read_text(encoding="utf-8") if (hm / ".claude" / "CLAUDE.md").exists() else ""
            check(r.returncode == 0 and "@~/.claude/ai-governance/GLOBAL-RULES.md" in md and str(hm) not in md,
                  "default dir under a home with %s: documented ~/ import, no machine path in CLAUDE.md" % ("spaces" if " " in name else "Unicode"))
            installed_state(hm / ".claude", expect_hook=True, home=hm)
            cmd = json.loads((hm / ".claude" / "settings.json").read_text())["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
            if shutil.which(cmd.split()[0]):
                p = subprocess.run(cmd, shell=True, input='{"prompt":"start"}', capture_output=True, text=True)
                check("SESSION_LIFECYCLE_START_TRIGGER" in p.stdout, "hook command string works through a shell with that path")
            else:
                report("NOT TESTED", "hook command run through a shell (%s not on PATH)" % cmd.split()[0])
        odd = tmp / "x y" / ".claude"
        inst(odd)
        t = (odd / "CLAUDE.md").read_text()
        check("x\\ y" in t, "config dir outside home with a space: path is backslash-escaped in the @import")
        installed_state(odd, expect_hook=False)

        print(" M. real Claude Code CLI loads a kit installed under a home folder with a space")
        if shutil.which("claude"):
            hm = tmp / "home with space"
            env = {"HOME": str(hm), "USERPROFILE": str(hm)}
            hm2 = hm / ".claude"
            if hm2.exists():
                loader_check(hm2, extra_env=env, label="[space in path] ")
                hook_check(hm2, extra_env=env, label="[space in path] ")
        else:
            report("NOT TESTED", "real Claude Code loader (claude CLI not on PATH)")

        print(" H. cross-platform handling (Windows: STATIC validation only, not executed on Windows)")
        spec = importlib.util.spec_from_file_location("kit_install", KIT / "install.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fake = type("R", (), {"cd": Path("/x/y z/.claude")})()
        orig_sys = mod.platform.system
        try:
            mod.platform.system = lambda: "Windows"
            wcmd = mod.hook_command(fake)
            mod.platform.system = lambda: "Linux"
            lcmd = mod.hook_command(fake)
        finally:
            mod.platform.system = orig_sys
        check(not wcmd.startswith('"') and wcmd.startswith(("python ", "py -3 ")) and "ai-governance/hooks/" in wcmd,
              "Windows hook command starts with a bare interpreter name (PowerShell + Git Bash safe)")
        check(lcmd.startswith('python3 "') and "y z" in lcmd, "POSIX hook command quotes paths containing spaces")
        win = tmp / "win"
        seed_config(win)
        c = json.loads((win / "settings.json").read_text())
        c["hooks"]["UserPromptSubmit"] = [{"hooks": [{"type": "command", "command":
            'python "C:\\Users\\a b\\.claude\\ai-governance\\hooks\\session-lifecycle-trigger.py"'}]}]
        (win / "settings.json").write_text(json.dumps(c))
        inst(win, "--hooks")
        n = json.loads((win / "settings.json").read_text())["hooks"]["UserPromptSubmit"]
        check(sum(len(g["hooks"]) for g in n) == 1, "a Windows-style (backslash) existing hook entry is recognised, not duplicated")
        check((KIT / "install.ps1").exists() and (KIT / "install.sh").exists(), "install.ps1 and install.sh wrappers present")
        report("NOT TESTED", "execution on real Windows (statically validated only)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- 3. target
def has_hook(cd):
    try:
        cfg = json.loads((cd / "settings.json").read_text(encoding="utf-8"))
        return any("ai-governance/hooks/session-lifecycle-trigger.py" in h.get("command", "").replace("\\", "/")
                   for g in cfg.get("hooks", {}).get("UserPromptSubmit", []) for h in g.get("hooks", []))
    except Exception:
        return False


def target(cd):
    print("\n[3] TARGET INSTALLATION (%s)" % cd)
    md = cd / "CLAUDE.md"
    has_block = md.exists() and "BEGIN AI-GOVERNANCE-STARTER-KIT" in md.read_text(encoding="utf-8")
    has_dir = (cd / "ai-governance").exists()
    if not has_block and not has_dir:
        report("NOT INSTALLED", "kit is not installed here. Run: python3 install.py --dry-run, then python3 install.py")
        return False
    installed_state(cd)
    return True


# ---------------------------------------------------------------- 4. runtime
def loader_check(cd, extra_env=None, label=""):
    """Ask the real Claude Code CLI what it loads (`/context`; needs no login and no model call)."""
    env = dict(os.environ, **(extra_env or {}))
    if not extra_env and cd != (Path.home() / ".claude").resolve():
        env["CLAUDE_CONFIG_DIR"] = str(cd)
    tmp = Path(tempfile.mkdtemp(prefix="kit-loader-"))
    try:
        (tmp / "CLAUDE.md").write_text("# loader check project\nProject canary code: ZEBRA-LOADER\n")
        r = subprocess.run(["claude", "-p", "/context"], cwd=str(tmp), env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=90)
        rows = [l for l in r.stdout.splitlines() if l.startswith("| User |") or l.startswith("| Project |")]
        if not rows:
            return report("NOT TESTED", "%sunrecognised `claude -p /context` output (Claude Code version differs)" % label)
        txt = "\n".join(rows + [l for l in r.stdout.splitlines() if l.startswith("| ponytail |")])
        check("| User |" in txt and "/CLAUDE.md" in txt, "%sClaude Code loads the user-level CLAUDE.md" % label)
        check("ai-governance/GLOBAL-RULES.md" in txt, "%sClaude Code resolved the @import and loads GLOBAL-RULES.md" % label)
        check("rules/ai-governance-coding.md" in txt, "%sClaude Code loads the user-level rule" % label)
        check("| Project |" in txt, "%sproject CLAUDE.md loads alongside the global rules" % label)
        check(re.search(r"\| ponytail \| User \|", r.stdout) is not None, "%sskill ponytail is discovered (source: User)" % label)
        return True
    except Exception as e:
        return report("NOT TESTED", "%sloader check could not run: %s" % (label, e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def hook_check(cd, extra_env=None, label=""):
    """Run the real Claude Code CLI on the prompt `start` and watch for the hook's output."""
    env = dict(os.environ, **(extra_env or {}))
    if not extra_env and cd != (Path.home() / ".claude").resolve():
        env["CLAUDE_CONFIG_DIR"] = str(cd)
    tmp = tempfile.mkdtemp(prefix="kit-hook-")
    seen = False
    try:
        p = subprocess.Popen(["claude", "-p", "start", "--output-format", "stream-json", "--verbose",
                              "--include-hook-events", "--model", "haiku", "--max-turns", "1"],
                             cwd=tmp, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)
        t0 = __import__("time").time()
        for line in p.stdout:
            if "SESSION_LIFECYCLE_START_TRIGGER" in line and "hook_response" in line:
                seen = True
                break
            if __import__("time").time() - t0 > 60:
                break
        p.terminate()
        p.wait(timeout=10)
    except Exception as e:
        return report("NOT TESTED", "%shook run could not execute: %s" % (label, e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return check(seen, "%sthe optional START/END hook fires inside Claude Code on `start`" % label)


def runtime(cd, live, installed):
    print("\n[4] RUNTIME INTEGRATION WITH CLAUDE CODE")
    if not installed:
        return report("NOT TESTED", "kit not installed in the target")
    if shutil.which("claude"):
        print("  Claude Code CLI loader check (offline: asks Claude Code what it loads; no login, no model call):")
        loader_check(cd)
        if has_hook(cd):
            hook_check(cd)
    else:
        report("NOT TESTED", "`claude` CLI not on PATH; loader check skipped (the VS Code extension bundles it, use the manual check)")
    if not live:
        report("MANUAL VERIFICATION REQUIRED", "VS Code extension and model behavior: start a NEW Claude Code session and ask:")
        print("      \"What is the AI Governance canary?\"   -> expect: %s" % CANARY)
        print("      (details: docs/VERIFY-IN-VSCODE.md, or run: python3 verify.py --live)")
        return
    if not shutil.which("claude"):
        return report("NOT TESTED", "`claude` CLI not on PATH (use docs/VERIFY-IN-VSCODE.md)")
    env = dict(os.environ)
    if cd != (Path.home() / ".claude").resolve():
        env["CLAUDE_CONFIG_DIR"] = str(cd)
    tmp = Path(tempfile.mkdtemp(prefix="kit-live-"))
    pc = "ZEBRA-%d" % random.randint(1000, 9999)
    try:
        newp, bare = tmp / "fresh-project", tmp / "bare-project"
        bare.mkdir()
        run([cd / "ai-governance" / "bootstrap-project.py", newp, "--name", "LiveCheck"])
        with open(newp / "CLAUDE.md", "a") as f:
            f.write("\n## Canary\nProject canary code: %s\n" % pc)
        q = ("Without using tools, one line: the AI Governance canary from your global rules and the project "
             "canary code from the project CLAUDE.md. Write MISSING for anything you cannot see.")

        def ask(cwd):
            r = subprocess.run(["claude", "-p", "--model", "haiku", "--max-turns", "2", q], cwd=str(cwd), env=env,
                               capture_output=True, text=True, timeout=180)
            return r.stdout + r.stderr

        a = ask(newp)
        if "Not logged in" in a or "/login" in a:
            return report("NOT TESTED", "Claude Code is not logged in for this config; log in, then re-run --live")
        check(CANARY in a, "new project inherits the global rules (canary seen)")
        check(pc in a, "project-specific rules load alongside the global rules")
        b = ask(bare)
        check(CANARY in b and pc not in b, "a project with no CLAUDE.md still inherits the global rules")
        if CANARY not in a:
            print("      model said: " + a.strip()[:300])
    except Exception as e:
        report("FAIL", "live check error: %s" % e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--no-sandbox", action="store_true")
    ap.add_argument("--claude-dir")
    a = ap.parse_args()
    cd = claude_dir(a.claude_dir)
    print("AI Governance Starter Kit %s - verification" % VERSION)
    package()
    if a.no_sandbox:
        print("\n[2] ISOLATED INSTALLATION TESTS")
        report("NOT TESTED", "skipped (--no-sandbox)")
    else:
        sandbox()
    installed = target(cd)
    runtime(cd, a.live, installed)
    counts = {s: STATUS.count(s) for s in dict.fromkeys(STATUS)}
    print("\nSummary: " + ", ".join("%d %s" % (n, s) for s, n in counts.items()))
    if "FAIL" in STATUS:
        return 1
    if "NOT INSTALLED" in STATUS:
        print("Package and sandbox checks are the release gate; the kit is simply not installed in the target yet.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
