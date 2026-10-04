#!/usr/bin/env python3
"""Secret leak check: make sure the model endpoint key / base URL never land in the repo, its history, or build output.

The secret VALUES are read at runtime only (never passed on the command line, never printed):
  - environment variables LLM_API_KEY and LLM_BASE_URL (the base URL's host is checked too), and/or
  - KEY=VALUE lines from the file named by $LEAK_CHECK_ENV_FILE (kept outside the repo), and/or
  - a file holding only the raw key, named by $LEAK_CHECK_KEY_FILE.
Output is only PASS / FAIL / SKIP with file or object names, never a value.

Usage (from track_2b/):  python3 scripts/leak_check.py [--tree] [--staged] [--history] [--path P ...] [--stdin]
  --tree     tracked + untracked (not ignored) files of the git work tree; ignored files are reported as INFO
  --staged   the staged diff (pre-commit)
  --history  every object in the git database (all refs, reflog, tags, stashes, dangling objects)
  --path P   any file or directory (PDFs: text via pdftotext + raw bytes; images: OCR via tesseract if installed)
  --stdin    scan standard input (e.g. a captured log piped in; nothing is written to disk)
Exit code: 0 = PASS (or SKIP when no secret values are available), 1 = FAIL."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

NAMES = ("LLM_API_KEY", "LLM_BASE_URL")
IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def load_needles() -> dict[str, bytes]:
    vals: dict[str, str] = {}
    f = os.environ.get("LEAK_CHECK_ENV_FILE")
    if f and Path(f).is_file():
        for line in Path(f).read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                k, v = k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'")
                if k in NAMES and v:
                    vals[k] = v
    kf = os.environ.get("LEAK_CHECK_KEY_FILE")          # optional: a file holding only the raw key
    if kf and Path(kf).is_file() and Path(kf).read_text().strip():
        vals.setdefault("LLM_API_KEY", Path(kf).read_text().strip())
    for k in NAMES:
        if os.environ.get(k) and k not in vals:
            vals[k] = os.environ[k]
    needles: dict[str, bytes] = {}
    if len(vals.get("LLM_API_KEY", "")) >= 8:
        needles["api key"] = vals["LLM_API_KEY"].encode()
    base = vals.get("LLM_BASE_URL", "")
    if base and "REPLACE" not in base and not base.startswith(("http://localhost", "http://127.")):
        needles["base url"] = base.rstrip("/").encode()
        host = urllib.parse.urlparse(base).hostname or ""
        if host and host not in ("localhost", "127.0.0.1"):
            needles["base url host"] = host.encode()
    return needles


def hits(data: bytes, needles: dict[str, bytes]) -> list[str]:
    low = data.lower()
    return [name for name, n in needles.items() if (n.lower() in low if name == "base url host" else n in data)]


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def file_texts(p: Path) -> list[tuple[str, bytes]]:
    """Raw bytes, plus extracted text for PDFs (pdftotext) and images (tesseract OCR) when the tools exist."""
    out = [("bytes", p.read_bytes())]
    suf = p.suffix.lower()
    if suf == ".pdf" and shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-q", str(p), "-"], capture_output=True)
        out.append(("pdf text", r.stdout))
    if suf in IMG and shutil.which("tesseract"):
        r = subprocess.run(["tesseract", str(p), "-", "--psm", "6"], capture_output=True)
        out.append(("ocr", r.stdout))
    return out


class Report:
    def __init__(self):
        self.failed = False

    def check(self, label: str, findings: list[str], scanned: int, info: list[str] | None = None):
        if findings:
            self.failed = True
            print(f"FAIL {label}: {len(findings)} finding(s) in {scanned} item(s)")
            for f in findings:
                print(f"  - {f}")
        else:
            print(f"PASS {label}: 0 findings in {scanned} item(s)")
        for i in info or []:
            print(f"  INFO {i}")


def scan_files(files: list[Path], needles, base: Path) -> tuple[list[str], int]:
    found, n = [], 0
    for p in files:
        if not p.is_file() or p.is_symlink():
            continue
        n += 1
        for kind, data in file_texts(p):
            for h in hits(data, needles):
                found.append(f"{p.relative_to(base) if p.is_relative_to(base) else p} [{kind}] contains the {h}")
    return found, n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=None, help="git repo root (default: discovered from cwd)")
    ap.add_argument("--tree", action="store_true")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument("--label", default=None, help="label for --stdin")
    a = ap.parse_args(argv)
    needles = load_needles()
    if not needles:
        print("SKIP leak check: no secret values available (set LLM_API_KEY / LLM_BASE_URL or LEAK_CHECK_ENV_FILE)")
        return 0
    print(f"leak check: {len(needles)} needle(s) loaded at runtime ({', '.join(needles)}); values are never printed")
    rep = Report()
    repo = None
    if a.tree or a.staged or a.history:
        repo = Path(a.repo or git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if a.tree:
        tracked = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")
        files = [repo / f.decode() for f in tracked if f]
        found, n = scan_files(files, needles, repo)
        ign = [repo / f.decode() for f in git(repo, "ls-files", "-z", "--others", "--ignored", "--exclude-standard").split(b"\0") if f]
        ifound, _ = scan_files(ign, needles, repo)
        rep.check(f"work tree ({repo.name})", found, n,
                  [f"git-ignored (cannot be committed): {x}" for x in ifound])
    if a.staged:
        diff = git(repo, "diff", "--cached", "--binary", "--no-color")
        names = git(repo, "diff", "--cached", "--name-only").decode().split()
        found = [f"staged diff contains the {h} (staged files: {', '.join(names) or '-'})" for h in hits(diff, needles)]
        for nm in names:   # name the offending staged file(s)
            p = repo / nm
            try:
                blob = git(repo, "show", f":{nm}")
            except subprocess.CalledProcessError:
                continue
            found += [f"staged {nm} contains the {h}" for h in hits(blob, needles)]
        rep.check("staged diff", found, len(names))
    if a.history:
        objs = git(repo, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)").decode().split("\n")
        objs = [o.split() for o in objs if o.strip()]
        found = []
        proc = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], input="\n".join(o[0] for o in objs).encode() + b"\n",
                              capture_output=True, check=True)
        data, i = proc.stdout, 0
        while i < len(data):
            nl = data.index(b"\n", i)
            sha, typ, size = data[i:nl].decode().split()
            body = data[nl + 1: nl + 1 + int(size)]
            i = nl + 1 + int(size) + 1
            for h in hits(body, needles):
                found.append(f"{typ} {sha[:12]} contains the {h}")
        refs = git(repo, "for-each-ref", "--format=%(refname)").decode().split()
        rlog = len(git(repo, "reflog", "--all", "--format=%H").split())
        rep.check(f"git database ({len(refs)} refs, {rlog} reflog entries, all objects incl. unreachable)", found, len(objs))
    for p in a.path:
        root = Path(p).resolve()
        files = [root] if root.is_file() else sorted(x for x in root.rglob("*") if ".git" not in x.relative_to(root).parts)
        found, n = scan_files(files, needles, root.parent)
        rep.check(f"path {root.name}", found, n)
    if a.stdin:
        data = sys.stdin.buffer.read()
        rep.check(a.label or "stdin", [f"input contains the {h}" for h in hits(data, needles)], 1)
    print("RESULT:", "FAIL" if rep.failed else "PASS")
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
