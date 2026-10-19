from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(os.getenv("ANGEL_DATA_DIR", str(Path.home() / "Angel_Platform"))).expanduser()
DB_PATH = DATA_DIR / "angel_intelligence.sqlite3"

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'Conversation',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'local',
    pinned INTEGER NOT NULL DEFAULT 0,
    project_id TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_time
ON messages(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS conversation_summaries (
    conversation_id TEXT PRIMARY KEY,
    message_count INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    approved INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user',
    deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    retrieval_policy_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    rating TEXT NOT NULL,
    correction TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tool_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    requested_by TEXT NOT NULL DEFAULT 'user',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_claims (
    id TEXT PRIMARY KEY,
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL CHECK(claim_type IN ('fact','inference')),
    verification_status TEXT NOT NULL DEFAULT 'supported' CHECK(verification_status IN ('supported','unverified','disputed','retracted')),
    scope_type TEXT NOT NULL DEFAULT 'conversation' CHECK(scope_type IN ('conversation','user','project','global')),
    scope_id TEXT NOT NULL,
    normalized_key TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT 'deterministic_rule' CHECK(created_by IN ('deterministic_rule','model','user','import')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_sources (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('message','document','document_chunk','tool_event','decision','claim')),
    source_id TEXT NOT NULL,
    relation TEXT NOT NULL CHECK(relation IN ('supports','contradicts','derived_from')),
    exact_quote TEXT NOT NULL DEFAULT '',
    source_start INTEGER,
    source_end INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY(claim_id) REFERENCES evidence_claims(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_claims_scope ON evidence_claims(scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_claims_normalized_key ON evidence_claims(normalized_key);
CREATE INDEX IF NOT EXISTS idx_claims_type_status ON evidence_claims(claim_type, verification_status);
CREATE INDEX IF NOT EXISTS idx_claim_sources_claim ON claim_sources(claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_sources_source ON claim_sources(source_type, source_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AngelDatabase:
    """Small, local SQLite persistence layer with thread-safe transactions."""

    def __init__(self, path: Path | str = DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript(_SCHEMA)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(conversations)").fetchall()}
            if "pinned" not in columns:
                connection.execute("ALTER TABLE conversations ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
            if "project_id" not in columns:
                connection.execute("ALTER TABLE conversations ADD COLUMN project_id TEXT NOT NULL DEFAULT ''")
            project_columns = {row[1] for row in connection.execute("PRAGMA table_info(projects)").fetchall()}
            if project_columns and "retrieval_policy_json" not in project_columns:
                connection.execute("ALTER TABLE projects ADD COLUMN retrieval_policy_json TEXT NOT NULL DEFAULT '{}'")
            if project_columns and "description" not in project_columns:
                connection.execute("ALTER TABLE projects ADD COLUMN description TEXT NOT NULL DEFAULT ''")

    def ensure_conversation(self, conversation_id: str, title: str = "Conversation") -> None:
        timestamp = _now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO conversations(id,title,created_at,updated_at)
                   VALUES(?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at""",
                (conversation_id, title or "Conversation", timestamp, timestamp),
            )

    def create_conversation(self, conversation_id: str, title: str = "New Chat") -> dict[str, Any]:
        """Create a conversation and return its metadata."""
        timestamp = _now()
        title = (title or "New Chat").strip()[:120] or "New Chat"
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO conversations(id,title,created_at,updated_at,source) VALUES(?,?,?,?,?)",
                (conversation_id, title, timestamp, timestamp, "local"),
            )
        return {"id": conversation_id, "title": title, "created_at": timestamp, "updated_at": timestamp, "source": "local"}

    def update_conversation_title(self, conversation_id: str, title: str) -> None:
        title = (title or "Conversation").strip()[:120] or "Conversation"
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
                (title, _now(), conversation_id),
            )

    def list_conversations(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT id,title,created_at,updated_at,source,pinned,project_id
                   FROM conversations ORDER BY pinned DESC, updated_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT id,title,created_at,updated_at,source,pinned,project_id FROM conversations WHERE id=?",
                (conversation_id,),
            ).fetchone()
        return dict(row) if row else None

    def set_conversation_project(self, conversation_id: str, project_id: str | None) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("UPDATE conversations SET project_id=?, updated_at=? WHERE id=?", (str(project_id or ""), _now(), conversation_id))

    def list_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._lock, self._connect() as connection:
            rows = connection.execute("SELECT id,name,description,retrieval_policy_json,created_at,updated_at FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        result=[]
        for row in rows:
            item=dict(row)
            item["retrieval_policy"] = json.loads(item.pop("retrieval_policy_json") or "{}")
            item["conversation_count"] = connection_count = 0
            with self._connect() as c:
                connection_count = c.execute("SELECT COUNT(*) FROM conversations WHERE project_id=?", (item["id"],)).fetchone()[0]
            item["conversation_count"] = int(connection_count)
            result.append(item)
        return result

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row=connection.execute("SELECT id,name,description,retrieval_policy_json,created_at,updated_at FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row: return None
        item=dict(row); item["retrieval_policy"]=json.loads(item.pop("retrieval_policy_json") or "{}")
        with self._lock, self._connect() as connection:
            item["conversation_count"]=int(connection.execute("SELECT COUNT(*) FROM conversations WHERE project_id=?", (project_id,)).fetchone()[0])
        return item

    def create_project(self, project_id: str, name: str, description: str = "", retrieval_policy: dict[str, Any] | None = None) -> dict[str, Any]:
        timestamp=_now(); name=(name or "Project").strip()[:120] or "Project"
        with self._lock, self._connect() as connection:
            connection.execute("INSERT INTO projects(id,name,description,retrieval_policy_json,created_at,updated_at) VALUES(?,?,?,?,?,?)", (project_id,name,description.strip()[:1000],json.dumps(retrieval_policy or {}, ensure_ascii=False),timestamp,timestamp))
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> dict[str, Any] | None:
        """Delete a project while preserving its conversations as global history."""
        project_id = str(project_id or "").strip()
        if not project_id:
            return None
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT id,name,description,retrieval_policy_json,created_at,updated_at FROM projects WHERE id=?",
                (project_id,),
            ).fetchone()
            if not row:
                return None
            conversation_count = int(connection.execute(
                "SELECT COUNT(*) FROM conversations WHERE project_id=?", (project_id,)
            ).fetchone()[0])
            # Project deletion must not destroy conversation history.
            connection.execute(
                "UPDATE conversations SET project_id='', updated_at=? WHERE project_id=?",
                (_now(), project_id),
            )
            connection.execute("DELETE FROM projects WHERE id=?", (project_id,))
        item = dict(row)
        item["retrieval_policy"] = json.loads(item.pop("retrieval_policy_json") or "{}")
        item["conversation_count"] = conversation_count
        return item

    def set_conversation_pinned(self, conversation_id: str, pinned: bool) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("UPDATE conversations SET pinned=?, updated_at=? WHERE id=?", (int(bool(pinned)), _now(), conversation_id))

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))
            return cursor.rowcount > 0

    def record_message(
        self,
        role: str,
        content: str,
        conversation_id: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        if role not in {"user", "assistant", "system", "tool"}:
            raise ValueError(f"Unsupported message role: {role}")
        self.ensure_conversation(conversation_id)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO messages(conversation_id,role,content,created_at,metadata_json)
                   VALUES(?,?,?,?,?)""",
                (conversation_id, role, content, _now(), json.dumps(metadata or {}, ensure_ascii=False)),
            )
            connection.execute(
                "UPDATE conversations SET updated_at=? WHERE id=?", (_now(), conversation_id)
            )
            return int(cursor.lastrowid)

    def list_messages(self, conversation_id: str = "default", limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 1000))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT id,conversation_id,role,content,created_at,metadata_json
                   FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?""",
                (conversation_id, limit),
            ).fetchall()
        result = []
        for row in reversed(rows):
            item = dict(row)
            item["time"] = item.pop("created_at")
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            result.append(item)
        return result

    def save_conversation_summary(self, conversation_id: str, message_count: int, summary: dict[str, Any], generated_at: str | None = None) -> None:
        timestamp = generated_at or _now()
        self.ensure_conversation(conversation_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO conversation_summaries(conversation_id,message_count,generated_at,summary_json)
                   VALUES(?,?,?,?)
                   ON CONFLICT(conversation_id) DO UPDATE SET
                     message_count=excluded.message_count,
                     generated_at=excluded.generated_at,
                     summary_json=excluded.summary_json""",
                (conversation_id, int(message_count), timestamp, json.dumps(summary, ensure_ascii=False)),
            )

    def get_conversation_summary(self, conversation_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT conversation_id,message_count,generated_at,summary_json FROM conversation_summaries WHERE conversation_id=?",
                (conversation_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["summary"] = json.loads(item.pop("summary_json") or "{}")
        return item

    def add_memory(self, content: str, category: str = "general", approved: bool = False, source: str = "user") -> int:
        timestamp = _now()
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO memories(content,category,approved,created_at,updated_at,source)
                   VALUES(?,?,?,?,?,?)""",
                (content, category, int(approved), timestamp, timestamp, source),
            )
            return int(cursor.lastrowid)

    def search_memories(self, query: str = "", limit: int = 10) -> list[dict[str, Any]]:
        terms = [part.lower() for part in query.split() if len(part) > 2]
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM memories WHERE approved=1 AND deleted=0
                   ORDER BY updated_at DESC LIMIT ?""", (max(1, min(int(limit), 100)),)
            ).fetchall()
        if not terms:
            return [dict(row) for row in rows]
        return [dict(row) for row in rows if all(term in row["content"].lower() for term in terms)]

    def record_feedback(self, rating: str, correction: str = "", message_id: int | None = None) -> int:
        if rating not in {"helpful", "incorrect", "incomplete"}:
            raise ValueError("Unsupported feedback rating")
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO feedback(message_id,rating,correction,created_at)
                   VALUES(?,?,?,?)""", (message_id, rating, correction, _now())
            )
            return int(cursor.lastrowid)

    def audit_tool(self, action: str, status: str, details: dict[str, Any] | None = None, requested_by: str = "user") -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO tool_audit(action,status,requested_by,details_json,created_at)
                   VALUES(?,?,?,?,?)""",
                (action, status, requested_by, json.dumps(details or {}, ensure_ascii=False), _now()),
            )
            return int(cursor.lastrowid)

    def integrity_check(self) -> str:
        """Return SQLite's built-in integrity result for this database."""
        with self._lock, self._connect() as connection:
            return str(connection.execute("PRAGMA integrity_check").fetchone()[0])

    def backup_to(self, destination: Path | str) -> Path:
        """Create a consistent SQLite backup using SQLite's online backup API."""
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)
        return destination

    def create_evidence_claim(self, *, claim_text: str, claim_type: str,
                              verification_status: str, scope_type: str, scope_id: str,
                              normalized_key: str, created_by: str, source_type: str,
                              source_id: str, relation: str, exact_quote: str = "") -> dict[str, Any]:
        import uuid
        timestamp = _now()
        claim_id = uuid.uuid4().hex
        source_id_value = uuid.uuid4().hex
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO evidence_claims
                   (id,claim_text,claim_type,verification_status,scope_type,scope_id,normalized_key,created_by,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (claim_id, claim_text, claim_type, verification_status, scope_type, scope_id,
                 normalized_key, created_by, timestamp, timestamp),
            )
            connection.execute(
                """INSERT INTO claim_sources
                   (id,claim_id,source_type,source_id,relation,exact_quote,created_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (source_id_value, claim_id, source_type, str(source_id), relation, exact_quote, timestamp),
            )
        return self.get_evidence_claim(claim_id) or {}

    def get_evidence_claim(self, claim_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT * FROM evidence_claims WHERE id=?", (claim_id,)).fetchone()
        return dict(row) if row else None

    def list_evidence_claims(self, *, scope_type: str | None = None, scope_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM evidence_claims WHERE 1=1"
        params: list[Any] = []
        if scope_type is not None:
            query += " AND scope_type=?"; params.append(scope_type)
        if scope_id is not None:
            query += " AND scope_id=?"; params.append(scope_id)
        query += " ORDER BY created_at ASC"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def find_evidence_claims(self, *, normalized_key: str, scope_type: str,
                             scope_id: str, verification_status: str = "supported") -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM evidence_claims
                   WHERE normalized_key=? AND scope_type=? AND scope_id=? AND verification_status=?
                   ORDER BY created_at ASC""",
                (normalized_key, scope_type, scope_id, verification_status),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_claim_sources(self, claim_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute("SELECT * FROM claim_sources WHERE claim_id=? ORDER BY created_at ASC", (claim_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_message(self, message_id: int) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT id,conversation_id,role,content,created_at,metadata_json FROM messages WHERE id=?",
                (int(message_id),),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        item["time"] = item.pop("created_at")
        return item

    def delete_evidence_claims(self, *, scope_type: str | None = None, scope_id: str | None = None) -> int:
        query = "DELETE FROM evidence_claims WHERE 1=1"; params: list[Any] = []
        if scope_type is not None:
            query += " AND scope_type=?"; params.append(scope_type)
        if scope_id is not None:
            query += " AND scope_id=?"; params.append(scope_id)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(query, params)
            return int(cursor.rowcount)

    def stats(self) -> dict[str, int | str]:
        with self._lock, self._connect() as connection:
            result: dict[str, int | str] = {"path": str(self.path)}
            for table in ("conversations", "messages", "memories", "knowledge_documents", "feedback", "tool_audit", "evidence_claims", "claim_sources"):
                result[table] = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            return result

    def migrate_history_json(self, history_path: Path | str) -> int:
        path = Path(history_path)
        if not path.exists():
            return 0
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return 0
        if not isinstance(records, list):
            return 0
        with self._lock, self._connect() as connection:
            existing = int(connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
        if existing:
            return 0
        imported = 0
        for record in records:
            if not isinstance(record, dict):
                continue
            role = str(record.get("role", "system"))
            content = str(record.get("content", ""))
            if role not in {"user", "assistant", "system", "tool"} or not content:
                continue
            self.record_message(role, content, str(record.get("conversation_id", "legacy")), {"source": "history_json"})
            imported += 1
        return imported


_default_database: AngelDatabase | None = None
_default_lock = threading.Lock()


def get_database() -> AngelDatabase:
    global _default_database
    if _default_database is None:
        with _default_lock:
            if _default_database is None:
                _default_database = AngelDatabase()
    return _default_database
