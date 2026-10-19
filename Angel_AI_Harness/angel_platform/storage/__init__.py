"""Persistent storage services for Angel Platform."""
from .database import AngelDatabase, get_database

__all__ = ["AngelDatabase", "get_database"]
