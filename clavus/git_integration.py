"""
Clavus — Git integration.

When you run `clavus snapshot`, it also commits the .als to git.
This gives you Ableton-aware snapshots + git's full version control.

The mapping:
  clavus init      → git init (if needed)
  clavus snapshot  → git add + git commit
  clavus branch    → git branch
  clavus checkout  → git checkout
  clavus merge     → git merge
  clavus push      → git push
  clavus pull      → git pull
  clavus log       → git log (alongside clavus log)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional


def _git(*args: str, cwd: Optional[Path] = None) -> tuple[int, str]:
    """Run a git command and return (returncode, output)."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        return -1, "git not found"
    except subprocess.TimeoutExpired:
        return -1, "git timed out"


def is_git_repo(path: Path) -> bool:
    """Check if path is inside a git repo."""
    code, _ = _git("rev-parse", "--git-dir", cwd=path)
    return code == 0


def git_init(path: Path) -> str:
    """Initialize a git repo if one doesn't exist."""
    if is_git_repo(path):
        return "already a git repo"
    code, out = _git("init", cwd=path)
    if code == 0:
        # Create a .gitignore for Ableton + OS files
        gitignore = path / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(
                "# Clavus auto-generated .gitignore\n"
                "# Ableton\n"
                "*.als.asd\n"
                "*.als.bak\n"
                "Backup/\n"
                "\n"
                "# OS\n"
                ".DS_Store\n"
                "Thumbs.db\n"
                "\n"
                "# Clavus store (shared via sync, not committed)\n"
                ".clavus/\n"
            )
            _git("add", ".gitignore", cwd=path)
        return "git repo initialized"
    return f"git init failed: {out}"


def git_commit(als_path: Path, message: str, author: str = "") -> str:
    """Add the .als file and commit with a message. Returns commit hash or error."""
    cwd = als_path.parent

    # Stage the .als file
    code, out = _git("add", als_path.name, cwd=cwd)
    if code != 0:
        return f"git add failed: {out}"

    # Check if anything changed
    code, out = _git("diff", "--cached", "--quiet", cwd=cwd)
    if code == 0:
        return ""  # nothing to commit (already up to date)

    # Commit
    commit_args = ["commit", "-m", f"clavus: {message}"]
    if author:
        commit_args += ["--author", author]
    code, out = _git(*commit_args, cwd=cwd)
    if code != 0:
        return f"git commit failed: {out}"

    # Extract commit hash
    code, hash_out = _git("rev-parse", "--short", "HEAD", cwd=cwd)
    return hash_out if code == 0 else "unknown"


def git_branch(action: str, name: str = "", cwd: Optional[Path] = None) -> str:
    """Wrapper around git branch commands."""
    if action == "create":
        code, out = _git("branch", name, cwd=cwd)
        return "ok" if code == 0 else out
    elif action == "delete":
        code, out = _git("branch", "-d", name, cwd=cwd)
        return "ok" if code == 0 else out
    elif action == "list":
        code, out = _git("branch", cwd=cwd)
        return out if code == 0 else ""
    return "unknown action"


def git_checkout(name: str, cwd: Optional[Path] = None) -> str:
    """Switch git branches."""
    code, out = _git("checkout", name, cwd=cwd)
    return "ok" if code == 0 else out


def git_merge(branch: str, cwd: Optional[Path] = None) -> str:
    """Merge a branch into current."""
    code, out = _git("merge", branch, cwd=cwd)
    if code == 0:
        return "ok"
    if "Already up to date" in out:
        return "already up to date"
    if "conflict" in out.lower():
        return f"merge conflict: {out[:200]}"
    return out


def git_push(remote: str = "origin", branch: str = "", cwd: Optional[Path] = None) -> str:
    """Push to remote."""
    args = ["push", remote]
    if branch:
        args.append(branch)
    code, out = _git(*args, cwd=cwd)
    return "ok" if code == 0 else out


def git_pull(remote: str = "origin", branch: str = "", cwd: Optional[Path] = None) -> str:
    """Pull from remote."""
    args = ["pull", remote]
    if branch:
        args.append(branch)
    code, out = _git(*args, cwd=cwd)
    return "ok" if code == 0 else out


def git_log(count: int = 10, cwd: Optional[Path] = None) -> list[dict]:
    """Get recent git log entries."""
    code, out = _git(
        "log", f"--max-count={count}",
        "--format=%h|%ai|%s",
        cwd=cwd,
    )
    if code != 0 or not out:
        return []

    entries = []
    for line in out.split("\n"):
        parts = line.split("|", 2)
        if len(parts) == 3:
            entries.append({
                "hash": parts[0],
                "date": parts[1][:10],
                "time": parts[1][11:16],
                "message": parts[2],
            })
    return entries
