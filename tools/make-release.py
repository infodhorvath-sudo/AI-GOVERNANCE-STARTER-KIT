#!/usr/bin/env python3
"""Maintainer tool: regenerate RELEASE-MANIFEST.json (and optionally the lightweight install ZIP).

  python3 tools/make-release.py              rewrite RELEASE-MANIFEST.json (describes the full Git tree)
  python3 tools/make-release.py --zip OUT    also build OUT: one top-level folder, deterministic

The ZIP is a lightweight installation package: docs/assets/branding/ (decorative PNGs) is omitted, README.md and
docs/INSTALLATION-GUIDE.md get their branding images replaced by links to the online copies, and the ZIP carries its own
RELEASE-MANIFEST.json listing exactly what it contains. Git keeps everything. Manifests never hash themselves.
"""
import hashlib, json, os, re, sys, zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "ai-governance-kit-backups"}
ZIP_OMIT = "docs/assets/branding/"
ONLINE = "https://github.com/infodhorvath-sudo/AI-GOVERNANCE-STARTER-KIT/blob/main/docs/assets/branding/"
BRAND_IMG = re.compile(r"!\[([^\]]*)\]\((?:docs/)?assets/branding/([^)\s]+)\)")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def files():
    return sorted(p for p in KIT.rglob("*") if p.is_file() and not (set(p.relative_to(KIT).parts) & SKIP_DIRS)
                  and p.name not in (".DS_Store", "RELEASE-MANIFEST.json") and p.suffix not in (".pyc", ".zip"))


def manifest(name_to_bytes, extra=None):
    m = {"name": "AI-GOVERNANCE-STARTER-KIT", "version": (KIT / "VERSION").read_text().strip(),
         "files": {k: sha(v) for k, v in name_to_bytes.items()}}
    m.update(extra or {})
    return (json.dumps(m, indent=2, sort_keys=True) + "\n").encode("utf-8")


def zip_content(rel, data):
    """Bytes as shipped in the ZIP: branding images become links to their online copies."""
    if rel in ("README.md", "docs/INSTALLATION-GUIDE.md"):
        text = BRAND_IMG.sub(lambda m: "*%s ([image online](%s%s))*" % (m.group(1), ONLINE, m.group(2)), data.decode("utf-8"))
        return text.encode("utf-8")
    return data


def main():
    fl = files()
    full = {p.relative_to(KIT).as_posix(): p.read_bytes() for p in fl}
    (KIT / "RELEASE-MANIFEST.json").write_bytes(manifest(full))
    print("manifest: %d files" % len(fl))
    if "--zip" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--zip") + 1])
        shipped = {k: zip_content(k, v) for k, v in full.items() if not k.startswith(ZIP_OMIT)}
        shipped["RELEASE-MANIFEST.json"] = manifest(
            {k: v for k, v in shipped.items()},
            {"package": "lightweight installation ZIP: decorative images omitted, see the Git repository"})
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for rel in sorted(shipped):
                zi = zipfile.ZipInfo("AI-GOVERNANCE-STARTER-KIT/" + rel, (2026, 11, 4, 0, 0, 0))
                zi.external_attr = (0o755 if os.access(KIT / rel, os.X_OK) else 0o644) << 16
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, shipped[rel])
        print("zip: %s (%d files, %d omitted)" % (out, len(shipped), len(full) - len(shipped) + 1))


if __name__ == "__main__":
    main()
