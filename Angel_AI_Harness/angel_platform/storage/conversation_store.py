from __future__ import annotations

from typing import Any

from .database import AngelDatabase, get_database


class ConversationStore:
    """Stable conversation boundary over Angel's existing SQLite store.

    Build 4.3.1-A intentionally keeps SQLite as the authoritative storage
    layer.  This service provides one application-facing interface so future
    context/intelligence work does not depend directly on database details.
    """

    def __init__(self, database: AngelDatabase | None = None):
        self.db = database or get_database()

    def create(self, conversation_id: str, title: str = "New Chat") -> dict[str, Any]:
        return self.db.create_conversation(conversation_id, title)

    def ensure(self, conversation_id: str | None, title: str = "New Chat") -> str:
        candidate = str(conversation_id or "").strip()
        if candidate and self.db.get_conversation(candidate):
            return candidate
        import uuid
        return self.create(uuid.uuid4().hex, title).get("id")

    def get(self, conversation_id: str) -> dict[str, Any] | None:
        return self.db.get_conversation(conversation_id)

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.db.list_conversations(limit)

    def messages(self, conversation_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.db.list_messages(conversation_id, limit)

    def append(self, conversation_id: str, role: str, content: str,
               metadata: dict[str, Any] | None = None) -> int:
        return self.db.record_message(role, content, conversation_id, metadata)

    def update_title(self, conversation_id: str, title: str) -> None:
        self.db.update_conversation_title(conversation_id, title)

    def set_project(self, conversation_id: str, project_id: str | None) -> None:
        self.db.set_conversation_project(conversation_id, project_id)

    def set_pinned(self, conversation_id: str, pinned: bool) -> None:
        self.db.set_conversation_pinned(conversation_id, pinned)

    def delete(self, conversation_id: str) -> bool:
        return self.db.delete_conversation(conversation_id)

    def stats(self) -> dict[str, int | str]:
        return self.db.stats()

    def integrity_check(self) -> str:
        return self.db.integrity_check()

    def backup_to(self, destination) -> str:
        return str(self.db.backup_to(destination))

    def migrate_legacy_history(self, history_path) -> int:
        return self.db.migrate_history_json(history_path)
