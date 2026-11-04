#!/usr/bin/env python3
"""Maintainer tool: regenerate RELEASE-MANIFEST.json (and optionally the ZIP).

  python3 tools/make-release.py              rewrite RELEASE-MANIFEST.json
  python3 tools/make-release.py --zip OUT    also build OUT (zip, one top-level folder)

Deterministic (sorted, fixed timestamps). The manifest never hashes itself.
"""
import hashlib, json, os, sys, zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "ai-governance-kit-backups"}


def files():
    return sorted(p for p in KIT.rglob("*") if p.is_file() and not (set(p.relative_to(KIT).parts) & SKIP_DIRS)
                  and p.name not in (".DS_Store", "RELEASE-MANIFEST.json") and p.suffix not in (".pyc", ".zip"))


def main():
    fl = files()
    man = {"name": "AI-GOVERNANCE-STARTER-KIT", "version": (KIT / "VERSION").read_text().strip(),
           "files": {p.relative_to(KIT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in fl}}
    (KIT / "RELEASE-MANIFEST.json").write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
    print("manifest: %d files" % len(fl))
    if "--zip" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--zip") + 1])
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in fl + [KIT / "RELEASE-MANIFEST.json"]:
                zi = zipfile.ZipInfo("AI-GOVERNANCE-STARTER-KIT/" + p.relative_to(KIT).as_posix(), (2026, 11, 4, 0, 0, 0))
                zi.external_attr = (0o755 if os.access(p, os.X_OK) else 0o644) << 16
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, p.read_bytes())
        print("zip:", out)


if __name__ == "__main__":
    main()
