"""Read-only, portable worktree audit. Never removes files or fetches refs."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip() or "git command failed")
    return result.stdout.decode("utf-8", "surrogateescape")


def worktrees(repo):
    return [dict(field.split(" ", 1) if " " in field else (field, "")
                 for field in block.split("\0") if field)
            for block in git(repo, "worktree", "list", "--porcelain", "-z").split("\0\0") if block]


def directory_size(path):
    size = 0
    def fail(error):
        raise error
    for root, _, files in os.walk(path, followlinks=False, onerror=fail):
        for name in files:
            item = Path(root) / name
            if not item.is_symlink():
                size += item.stat().st_size
    return size


def last_chat(path, exports):
    if not exports:
        return 0
    normalized = str(path).replace("\\", "/")
    matcher = re.compile(re.escape(normalized) + r'(?=[/"\s]|$)', re.I if os.name == "nt" else 0)
    latest = 0
    def fail(error):
        raise error
    for root, _, files in os.walk(exports, followlinks=False, onerror=fail):
        for name in files:
            item = Path(root) / name
            if item.is_symlink():
                continue
            with item.open(encoding="utf-8", errors="replace") as stream:
                if any(matcher.search(line.replace("\\\\", "\\").replace("\\", "/")) for line in stream):
                    latest = max(latest, item.stat().st_mtime)
    return latest


def audit(repo, base=None, exports=None, with_prs=True):
    trees = worktrees(repo)
    if base is None:
        for candidate in ("origin/HEAD", "origin/main", "origin/master", "main", "master"):
            try:
                git(repo, "rev-parse", "--verify", candidate)
                base = candidate
                break
            except RuntimeError:
                pass
    elif base.startswith("-"):
        raise ValueError("base must be a ref, not an option")
    if base:
        git(repo, "rev-parse", "--verify", base)
    print(f"Audit base: {base or 'unavailable'}. Local refs only; remote data can be stale.", file=sys.stderr)
    prs = []
    if with_prs and shutil.which("gh"):
        try:
            result = subprocess.run(["gh", "pr", "list", "--state", "all", "--limit", "1000",
                                     "--json", "number,state,headRefName"], cwd=repo,
                                    capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
            prs = json.loads(result.stdout)
            if not isinstance(prs, list) or any(
                not isinstance(pr, dict) or not isinstance(pr.get("number"), int)
                or not isinstance(pr.get("headRefName"), str)
                or pr.get("state") not in {"OPEN", "CLOSED", "MERGED"} for pr in prs
            ):
                raise ValueError("invalid PR data")
        except (subprocess.SubprocessError, ValueError):
            prs = []
            print("Warning: PR state unavailable.", file=sys.stderr)
    rows = []
    for tree in trees[1:]:
        path = Path(tree["worktree"])
        row = dict(size=-1, age="?", merged="?", dirty="?", remote="?", pr="-", last="-", bucket="review", path=str(path))
        try:
            row["size"] = directory_size(path)
            stamp = int(git(path, "log", "-1", "--format=%ct").strip())
            row["age"] = f"{max(0, int((time.time() - stamp) / 86400))}d"
            status = git(path, "status", "--porcelain", "-z", "--ignored=matching").split("\0")
            counts = {"wip": 0, "untracked": 0, "ignored": 0}
            index = 0
            while index < len(status) and status[index]:
                code = status[index][:2]
                counts["untracked" if code == "??" else "ignored" if code == "!!" else "wip"] += 1
                index += 2 if "R" in code or "C" in code else 1
            row["dirty"] = ",".join(f"{key}:{count}" for key, count in counts.items() if count) or "clean"
            if base:
                result = subprocess.run(["git", "-C", str(path), "merge-base", "--is-ancestor", "HEAD", base], capture_output=True, timeout=30)
                row["merged"] = {0: "YES", 1: "no"}.get(result.returncode, "?")
            branch = tree.get("branch", "").removeprefix("refs/heads/")
            row["remote"] = "detached" if not branch else "no-remote"
            if branch:
                try:
                    behind, ahead = git(path, "rev-list", "--left-right", "--count", f"refs/remotes/origin/{branch}...HEAD").split()
                    row["remote"] = "pushed" if behind == ahead == "0" else f"ahead:{ahead},behind:{behind}"
                except RuntimeError:
                    pass
            matches = [pr for pr in prs if pr["headRefName"] == branch]
            row["pr"] = ",".join(f'#{pr["number"]}/{pr["state"]}' for pr in matches) or "-"
            latest = last_chat(path, exports)
            if latest:
                row["last"] = datetime.fromtimestamp(latest, timezone.utc).strftime("%Y-%m-%d")
            if counts["wip"]:
                row["bucket"] = "hold-wip"
            elif counts["untracked"] or counts["ignored"]:
                row["bucket"] = "hold-local-files"
            elif any(pr["state"] == "OPEN" for pr in matches):
                row["bucket"] = "hold-open-pr"
            elif latest and time.time() - latest <= 4 * 86400:
                row["bucket"] = "verify-recent-chat"
            elif row["merged"] == "YES":
                row["bucket"] = "verify-history"
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            row["bucket"] = "hold-audit-error"
            print(f"Warning: {path}: {error}", file=sys.stderr)
        rows.append(row)
    return sorted(rows, key=lambda row: row["size"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--base")
    parser.add_argument("--skip-prs", action="store_true")
    parser.add_argument("--transcripts-dir", default=os.environ.get("PSTACK_TRANSCRIPTS_DIR"))
    args = parser.parse_args()
    if args.transcripts_dir and not Path(args.transcripts_dir).is_dir():
        parser.error("transcripts-dir must be an explicitly selected project export directory")
    try:
        rows = audit(Path(args.repo).resolve(), args.base, args.transcripts_dir, not args.skip_prs)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
    print("SIZE_BYTES\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE")
    for row in rows:
        print("\t".join(str(row[key]).replace("\t", " ").replace("\n", " ").replace("\r", " ")
                        for key in ("size", "age", "merged", "dirty", "remote", "pr", "last", "bucket", "path")))


if __name__ == "__main__":
    main()
