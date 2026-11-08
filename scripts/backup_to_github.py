#!/usr/bin/env python3
"""Backup template: copy YOUR OWN data to YOUR OWN *private* GitHub repo.

Usage (needs git and an authenticated `gh` CLI):
  scripts/backup_to_github.py --repo <owner>/<private-repo> [--src PATH ...] [--create] [--dry-run]

Defaults: --src = $XUAN_HOME (~/.local/share/tianji-xuan), working clone in
~/.local/share/xuan-backup-clone (override with --workdir).

Safety rules:
- refuses unless GitHub reports the repo as PRIVATE (checked before every push);
- refuses if the target equals this code repo's remotes or the upstream engine repo;
- skips credential-like filenames and files whose contents look like tokens/keys;
- skips files larger than --max-mb (default 50) and excluded dirs (env, caches);
- writes BACKUP_MANIFEST.json listing every skipped item and why;
- never deletes anything from the source paths.
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys
from datetime import datetime, timezone

P = pathlib.Path
ROOT = P(__file__).resolve().parent.parent
UPSTREAMS = {"renhuai123/ziwei-doushu"}
EXDIR = {".git", "node_modules", "__pycache__", ".venv", "venv", "xuan-venv", ".cache", "cache",
         "build", "dist", "out", "target", ".pytest_cache", ".mypy_cache", "engine"}
BADNAME = re.compile(r"(^\.env(\.|$)|(^|[-_.])(credentials?|secrets?|cookies?|tokens?|passwords?)([-_.]|$)"
                     r"|^(id_rsa|id_ed25519|id_ecdsa)(\.pub)?$|^\.netrc$|^\.npmrc$|^\.pypirc$)", re.I)
BADSUFFIX = {".pem", ".key", ".p12", ".pfx", ".keystore", ".jks", ".kdbx"}
SECRETS = [re.compile(p) for p in (
    rb"gh[pousr]_[A-Za-z0-9]{20,}", rb"github_pat_[A-Za-z0-9_]{20,}",
    rb"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}", rb"\bxox[baprs]-[A-Za-z0-9-]{20,}",
    rb"AKIA[A-Z0-9]{16}", rb"AIza[0-9A-Za-z_-]{35}",
    rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    rb"(?i)(?:api[_-]?key|api[_-]?secret|access[_-]?token|client[_-]?secret|passphrase|password)"
    rb"[\"']?\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']")]


def sh(args, **kw):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kw).stdout.strip()


def norm(repo):
    m = re.search(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", repo)
    return (m.group(1) if m else repo).lower()


def forbidden_targets():
    out = set(UPSTREAMS)
    try:
        for line in sh(["git", "-C", str(ROOT), "remote", "-v"]).splitlines():
            out.add(norm(line.split()[1]))
    except Exception:
        pass
    return out


def assert_private(repo):
    info = json.loads(sh(["gh", "repo", "view", repo, "--json", "nameWithOwner,isPrivate,visibility"]))
    if not (info.get("isPrivate") is True and info.get("visibility") == "PRIVATE"):
        sys.exit(f"ABORT: {repo} is not private / 目标库不是私有库，拒绝备份")


def has_secret(path):
    prev = b""
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            data = prev + chunk
            if any(p.search(data) for p in SECRETS):
                return True
            prev = data[-512:]
    return False


def collect(srcs, max_bytes):
    keep, skipped = [], []
    for src in srcs:
        src = P(src).expanduser().resolve()
        if not src.exists():
            skipped.append({"path": str(src), "reason": "source not found"}); continue
        files = [src] if src.is_file() else None
        base = src.parent if src.is_file() else src
        if files is None:
            files = []
            for dp, dns, fns in os.walk(src):
                for d in list(dns):
                    if d in EXDIR:
                        skipped.append({"path": str(P(dp, d)), "reason": "excluded directory"}); dns.remove(d)
                files += [P(dp, f) for f in fns]
        for f in files:
            rel = P(src.name) / f.relative_to(base) if src.is_dir() else P(f.name)
            if f.is_symlink() or not f.is_file():
                reason = "symlink or special file"
            elif BADNAME.search(f.name) or f.suffix.lower() in BADSUFFIX:
                reason = "credential-like filename"
            elif f.stat().st_size > max_bytes:
                reason = f"larger than {max_bytes // (1 << 20)} MB ({f.stat().st_size} bytes)"
            elif has_secret(f):
                reason = "content looks like a secret"
            else:
                keep.append((f, rel)); continue
            skipped.append({"path": str(f), "reason": reason})
    return keep, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("XUAN_BACKUP_REPO"), help="owner/name of YOUR private repo")
    ap.add_argument("--src", action="append", help="path to back up (repeatable); default $XUAN_HOME")
    ap.add_argument("--workdir", default=os.path.expanduser("~/.local/share/xuan-backup-clone"))
    ap.add_argument("--max-mb", type=int, default=50)
    ap.add_argument("--create", action="store_true", help="create the repo as private if it does not exist")
    ap.add_argument("--dry-run", action="store_true", help="scan and write manifest only; no git operations")
    a = ap.parse_args()
    if not a.repo or "/" not in a.repo:
        sys.exit("need --repo <owner>/<name> (or XUAN_BACKUP_REPO)")
    repo = norm(a.repo)
    if repo in forbidden_targets():
        sys.exit(f"ABORT: {repo} is this code repo or an upstream; refusing / 不能备份到代码库或上游库")
    srcs = a.src or [os.environ.get("XUAN_HOME", "~/.local/share/tianji-xuan")]
    keep, skipped = collect(srcs, a.max_mb << 20)
    manifest = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "sources": [str(P(s).expanduser()) for s in srcs],
                "files": len(keep), "skipped": skipped}
    print(f"{len(keep)} files to back up, {len(skipped)} skipped")
    for s in skipped:
        print(f"  skip: {s['path']}  ({s['reason']})")
    if a.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2)); return
    wd = P(a.workdir).expanduser()
    if a.create and subprocess.run(["gh", "repo", "view", repo], capture_output=True).returncode != 0:
        sh(["gh", "repo", "create", repo, "--private"])
    assert_private(repo)
    url = f"https://github.com/{repo}.git"
    if not (wd / ".git").exists():
        wd.parent.mkdir(parents=True, exist_ok=True)
        sh(["gh", "repo", "clone", repo, str(wd)])
    if norm(sh(["git", "-C", str(wd), "remote", "get-url", "origin"])) != repo:
        sys.exit(f"ABORT: {wd} origin is not {repo}")
    for item in wd.iterdir():  # mirror: clear the clone (not the sources)
        if item.name != ".git":
            shutil.rmtree(item) if item.is_dir() and not item.is_symlink() else item.unlink()
    for f, rel in keep:
        dst = wd / "data" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    (wd / "BACKUP_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sh(["git", "-C", str(wd), "add", "-A"])
    if not sh(["git", "-C", str(wd), "status", "--porcelain"]):
        print("no changes"); return
    sh(["git", "-C", str(wd), "commit", "-q", "-m", f"backup {manifest['time']}"])
    assert_private(repo)  # re-check right before pushing
    sh(["git", "-C", str(wd), "push", "-q", url, "HEAD"])
    print(f"pushed to private repo {repo}")


if __name__ == "__main__":
    main()
