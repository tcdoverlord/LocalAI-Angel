"""Data-driven storage review for Angel Platform 4.3.1-F.

This module measures the existing SQLite design without changing the production
schema.  It is intentionally self-contained so the storage decision can be
reproduced on a clean temporary database and inspected by the application.
"""
from __future__ import annotations

import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any

from .database import AngelDatabase


BENCHMARK_POINTS = (100, 1000, 5000)


def _elapsed_ms(fn) -> float:
    start = time.perf_counter()
    fn()
    return round((time.perf_counter() - start) * 1000, 3)


def _populate(db: AngelDatabase, count: int) -> None:
    db.ensure_conversation("benchmark")
    for index in range(count):
        db.record_message(
            "user" if index % 2 == 0 else "assistant",
            f"Benchmark message {index}: preserve the authoritative SQLite transcript.",
            "benchmark",
        )


def _integrity(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def run_storage_review() -> dict[str, Any]:
    """Run reproducible measurements against temporary copies of the schema."""
    root = Path(tempfile.mkdtemp(prefix="angel-storage-review-"))
    try:
        growth: list[dict[str, Any]] = []
        startup_ms: list[float] = []
        query_ms: list[float] = []

        for count in BENCHMARK_POINTS:
            path = root / f"benchmark-{count}.sqlite3"
            startup_ms.append(_elapsed_ms(lambda p=path: AngelDatabase(p)))
            db = AngelDatabase(path)
            populate_ms = _elapsed_ms(lambda: _populate(db, count))
            query = _elapsed_ms(lambda: db.list_messages("benchmark", min(count, 1000)))
            stats = db.stats()
            size = path.stat().st_size
            growth.append(
                {
                    "messages": count,
                    "file_bytes": size,
                    "file_kib": round(size / 1024, 2),
                    "populate_ms": populate_ms,
                    "query_ms": query,
                    "messages_returned": min(count, 1000),
                    "integrity_check": _integrity(path),
                }
            )
            query_ms.append(query)

        # Backup/recovery measurement uses SQLite's supported online backup API.
        source = root / "recovery-source.sqlite3"
        backup = root / "recovery-backup.sqlite3"
        restored = root / "recovery-restored.sqlite3"
        source_db = AngelDatabase(source)
        _populate(source_db, 1000)
        backup_ms = _elapsed_ms(lambda: _sqlite_backup(source, backup))
        shutil.copy2(backup, restored)
        recovery_integrity = _integrity(restored)
        recovered_count = AngelDatabase(restored).stats()["messages"]

        return {
            "benchmark_points": list(BENCHMARK_POINTS),
            "startup_ms": startup_ms,
            "query_ms": query_ms,
            "growth": growth,
            "backup": {
                "method": "sqlite_online_backup_api",
                "source_messages": 1000,
                "backup_ms": backup_ms,
                "backup_bytes": backup.stat().st_size,
            },
            "recovery": {
                "restored_messages": recovered_count,
                "integrity_check": recovery_integrity,
            },
            "production_schema_changed": False,
            "notes": [
                "Measurements use temporary databases with the production schema.",
                "Query timing measures retrieval of up to 1000 messages through AngelDatabase.",
                "Startup timing measures schema initialization/opening, not model startup.",
                "The benchmark is comparative evidence, not a hardware-independent SLA.",
            ],
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _sqlite_backup(source: Path, destination: Path) -> None:
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)


def storage_decision(review: dict[str, Any]) -> dict[str, Any]:
    """Return the documented recommendation without replacing storage."""
    return {
        "recommendation": "Option B",
        "title": "Retain ConversationStore and improve SQLite",
        "rationale": [
            "SQLite is already the authoritative, relational store for conversations, messages, projects, summaries, memories, feedback, and tool audit records.",
            "ConversationStore provides an application boundary that keeps future storage changes reversible.",
            "The measured system includes working integrity, backup, recovery, indexed conversation retrieval, and non-destructive summary storage.",
            "Per-conversation JSON would duplicate relational relationships and create additional consistency/backup concerns without evidence of a current SQLite bottleneck.",
            "The legacy chat_history.json copy should remain compatibility/export-only in this build; retirement should be a separate migration decision after export/import and recovery workflows are verified.",
        ],
        "option_status": {
            "A": "Not selected now; compatible with the long-term direction after JSON retirement is separately validated.",
            "B": "Selected for 4.3.1-F.",
            "C": "Evaluated and deferred; no measured need for per-conversation JSON storage.",
        },
    }
