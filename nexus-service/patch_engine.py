"""
Angel Nexus Change Control Engine.

Safe-by-default patch processor:
- JSON patch manifests
- exact-match file edits
- path allow-list enforcement
- dated Git safe points
- validation commands
- automatic rollback on failure
- append-only patch ledger

This module intentionally does not execute arbitrary commands from a patch
manifest. Validation commands are selected from a trusted server-side profile.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("NEXUS_TARGET_ROOT", "/workspace")).resolve()
DATA_ROOT = Path(os.environ.get("NEXUS_DATA_ROOT", "/data")).resolve()
PATCH_ROOT = (DATA_ROOT / "patches").resolve()
LEDGER = PATCH_ROOT / "patch-ledger.jsonl"
SAFE_POINTS = (PATCH_ROOT / "safe-points").resolve()

ALLOWED_VALIDATIONS = {
    "python_compile": ["python", "-m", "compileall", "-q", "."],
    "git_diff_check": ["git", "diff", "--check"],
    "frontend_lint": ["npm", "run", "lint", "--prefix", "core/http/react-ui"],
    "frontend_build": ["npm", "run", "build", "--prefix", "core/http/react-ui"],
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def safe_relative_path(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Unsafe path: {value}")
    resolved = (ROOT / candidate).resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        raise ValueError(f"Path escapes target root: {value}")
    return candidate

def append_ledger(event: dict[str, Any]) -> None:
    PATCH_ROOT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": utc_now(), **event}) + "\n")

def run_git(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

def create_safe_point(patch_id: str) -> dict[str, Any]:
    if not (ROOT / ".git").exists():
        raise RuntimeError("Target root is not a Git repository.")
    status = run_git("status", "--porcelain")
    if status.stdout.strip():
        raise RuntimeError(
            "Target repository has uncommitted changes. Commit or stash them before "
            "creating a safe point; automatic rollback must never destroy existing work."
        )
    snapshot = {
        "safe_point_id": f"{stamp()}-{patch_id}",
        "patch_id": patch_id,
        "created_at": utc_now(),
        "root": str(ROOT),
        "head": run_git("rev-parse", "HEAD").stdout.strip(),
        "status_before": status.stdout,
    }
    SAFE_POINTS.mkdir(parents=True, exist_ok=True)
    output = SAFE_POINTS / f"{snapshot['safe_point_id']}.json"
    output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    append_ledger({"event": "safe_point_created", **snapshot})
    return snapshot

def load_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    required = ["patch_id", "title", "changes"]
    missing = [key for key in required if key not in manifest]
    if missing:
        raise ValueError(f"Missing manifest fields: {', '.join(missing)}")
    if not isinstance(manifest["changes"], list) or not manifest["changes"]:
        raise ValueError("changes must be a non-empty list.")
    return manifest

def apply_change(change: dict[str, Any]) -> list[str]:
    operation = change.get("operation")
    relative = safe_relative_path(change.get("file", ""))
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)

    if operation == "replace_exact":
        if not target.is_file():
            raise ValueError(f"Target file does not exist: {relative}")
        original = target.read_text(encoding="utf-8")
        expected = change.get("expected")
        replacement = change.get("replacement")
        if not isinstance(expected, str) or not isinstance(replacement, str):
            raise ValueError("replace_exact requires expected and replacement strings.")
        occurrences = original.count(expected)
        if occurrences != 1:
            raise ValueError(
                f"Expected exactly one match in {relative}; found {occurrences}."
            )
        target.write_text(original.replace(expected, replacement, 1), encoding="utf-8")
        return [relative.as_posix()]

    if operation == "append_file":
        content = change.get("content")
        if not isinstance(content, str):
            raise ValueError("append_file requires string content.")
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
        return [relative.as_posix()]

    if operation == "create_file":
        if target.exists():
            raise ValueError(f"Refusing to overwrite existing file: {relative}")
        content = change.get("content")
        if not isinstance(content, str):
            raise ValueError("create_file requires string content.")
        target.write_text(content, encoding="utf-8")
        return [relative.as_posix()]

    raise ValueError(f"Unsupported operation: {operation}")

def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest = load_manifest(manifest)
    touched = []
    for change in manifest["changes"]:
        safe_relative_path(change.get("file", ""))
        touched.append(change.get("file"))
    validations = manifest.get("validation_profiles", ["git_diff_check"])
    unknown = [name for name in validations if name not in ALLOWED_VALIDATIONS]
    if unknown:
        raise ValueError(f"Unknown validation profiles: {', '.join(unknown)}")
    return {
        "valid": True,
        "patch_id": manifest["patch_id"],
        "title": manifest["title"],
        "files": touched,
        "validation_profiles": validations,
    }

def execute_validation(profiles: list[str]) -> list[dict[str, Any]]:
    results = []
    for profile in profiles:
        command = ALLOWED_VALIDATIONS[profile]
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        results.append({
            "profile": profile,
            "command": command,
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        })
        if result.returncode != 0:
            break
    return results

def apply_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest = load_manifest(manifest)
    validation = validate_manifest(manifest)
    safe_point = create_safe_point(manifest["patch_id"])
    changed = []
    validation_results = []
    try:
        for change in manifest["changes"]:
            changed.extend(apply_change(change))
        validation_results = execute_validation(
            manifest.get("validation_profiles", ["git_diff_check"])
        )
        passed = bool(validation_results) and all(
            item["passed"] for item in validation_results
        )
        if not passed:
            rollback_to_safe_point(safe_point)
            result = {
                "status": "ROLLED_BACK",
                "patch_id": manifest["patch_id"],
                "safe_point": safe_point,
                "changed_files": changed,
                "validation": validation_results,
            }
            append_ledger({"event": "patch_rolled_back", **result})
            return result

        result = {
            "status": "VALIDATED",
            "patch_id": manifest["patch_id"],
            "title": manifest["title"],
            "safe_point": safe_point,
            "changed_files": changed,
            "validation": validation_results,
            "next_step": "Review the diff, then commit through the normal Git workflow.",
        }
        append_ledger({"event": "patch_validated", **result})
        return result
    except Exception as exc:
        rollback_to_safe_point(safe_point)
        result = {
            "status": "ROLLED_BACK",
            "patch_id": manifest["patch_id"],
            "safe_point": safe_point,
            "changed_files": changed,
            "error": str(exc),
            "validation": validation_results,
        }
        append_ledger({"event": "patch_error_rolled_back", **result})
        return result

def rollback_to_safe_point(safe_point: dict[str, Any]) -> None:
    expected_head = safe_point.get("head")
    current_head = run_git("rev-parse", "HEAD").stdout.strip()
    if expected_head and current_head != expected_head:
        raise RuntimeError(
            "Refusing automatic rollback because HEAD changed during patch execution."
        )
    result = run_git("reset", "--hard", expected_head)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Git rollback failed.")
    result = run_git("clean", "-fd")
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Git clean failed.")

def read_ledger(limit: int = 100) -> list[dict[str, Any]]:
    if not LEDGER.exists():
        return []
    rows = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
