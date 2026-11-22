#!/usr/bin/env python3
"""Push to netadminplus/ramtiin.ir via the Git Data API.

Repo layout (since the 2026-11-22 split):
- `main`     = source: build.py, push.py, the WordPress export JSONs,
               media/, theme/, README.md / README-en.md.
- `gh-pages` = the built static site (what GitHub Pages serves).
  Repo root on that branch == the built site (pre-rendered HTML, no
  build step on GitHub); custom domain ramtiin.ir via the CNAME file.

Default run pushes the built site to gh-pages (rebuild with build.py
first). To push the source tree to main: python3 push.py --src . --branch main

Usage: python3 push.py [--message "msg"] [--branch gh-pages] [--src site]
Uses the stored custom.github credential via the surrogate exchange.
"""
import argparse
import base64
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
REPO = "netadminplus/ramtiin.ir"
API = "https://api.github.com"

SKIP_DIRS = {"__pycache__", ".git"}
# Top-level entries never pushed when the source tree itself is the
# source (--src .): the build output, local-only data and dev artifacts.
SKIP_TOP = {"site", "__pycache__", ".git", "media-originals",
            "pages_html", "figma-output", "readme-drafts"}
SKIP_FILES = {"verify_report.json", "missing_uploads.json"}
SKIP_SUFFIXES = (".pyc",)


def api(method, path, body=None):
    """GitHub API call with retries on transient 5xx (a 502 mid-push used to
    abort the whole 421-blob upload with nothing committed). Blob/tree/
    commit POSTs are idempotent or harmless to duplicate, so retrying is
    safe; the ref update is the only step that must happen once, and it
    runs last."""
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for attempt in range(4):
        req = urllib.request.Request(API + path, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (502, 503, 504) and attempt < 3:
                wait = 5 * (2 ** attempt)
                print(f"HTTP {e.code} {method} {path}: retrying in {wait}s (attempt {attempt + 2}/4)", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"HTTP {e.code} {method} {path}: {e.read().decode()[:300]}", file=sys.stderr)
            raise
    raise last


def collect_files(root):
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.parts[0] in SKIP_TOP:
            continue
        if rel.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.suffix in SKIP_SUFFIXES:
            continue
        if rel.name == ".DS_Store":
            continue
        files.append((str(rel), p))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", default="Static rebuild of ramtiin.ir (WordPress -> GitHub Pages)")
    ap.add_argument("--branch", default="gh-pages")
    ap.add_argument("--src", default="site",
                    help="directory to push: 'site' (built site) or '.' (source tree)")
    args = ap.parse_args()

    src_root = (HERE / args.src).resolve()
    files = collect_files(src_root)
    print(f"{len(files)} files to push from {args.src} to {args.branch}")

    parents = []
    try:
        ref = api("GET", f"/repos/{REPO}/git/ref/heads/{args.branch}")
        parents = [ref["object"]["sha"]]
        print("parent commit:", parents[0][:12])
    except urllib.error.HTTPError as e:
        if e.code in (404, 409):
            print("no existing branch -- bootstrapping with an initial commit")
            readme_path = SITE / "README.md"
            if not readme_path.exists():
                readme_path = HERE / "README.md"
            readme = readme_path.read_bytes()
            api("PUT", f"/repos/{REPO}/contents/README.md",
                {"message": "Initial commit", "content": base64.b64encode(readme).decode()})
            ref = api("GET", f"/repos/{REPO}/git/ref/heads/{args.branch}")
            parents = [ref["object"]["sha"]]
            print("bootstrap commit:", parents[0][:12])
        else:
            raise

    blobs = []
    for rel, path in files:
        raw = path.read_bytes()
        b = api("POST", f"/repos/{REPO}/git/blobs",
                {"content": base64.b64encode(raw).decode(), "encoding": "base64"})
        blobs.append({"path": rel, "mode": "100644", "type": "blob", "sha": b["sha"]})
    print(f"{len(blobs)} blobs created")
    tree = api("POST", f"/repos/{REPO}/git/trees", {"tree": blobs})
    print("tree:", tree["sha"][:12])

    commit = api("POST", f"/repos/{REPO}/git/commits",
                 {"message": args.message, "tree": tree["sha"], "parents": parents})
    print("commit:", commit["sha"])
    api("PATCH", f"/repos/{REPO}/git/refs/heads/{args.branch}", {"sha": commit["sha"]})
    print(f"pushed to {REPO}@{args.branch}: {commit['sha']}")
    print(f"https://github.com/{REPO}/commit/{commit['sha']}")


if __name__ == "__main__":
    main()
