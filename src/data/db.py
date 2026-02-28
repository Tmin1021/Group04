"""
Database helper (PostgreSQL via psycopg).

This is optional for the assignment if you already have CSVs.
Do NOT commit real credentials to GitHub.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
import json
from pathlib import Path
import psycopg

@dataclass
class DBInfo:
    host: str
    port: int
    database: str
    user: str
    password: str

    @staticmethod
    def from_json(path: str | Path) -> "DBInfo":
        data = json.loads(Path(path).read_text())
        return DBInfo(
            host=data["host"],
            port=int(data["port"]),
            database=data["database"],
            user=data["user"],
            password=data["password"],
        )

def connect(db: DBInfo) -> psycopg.Connection:
    return psycopg.connect(
        host=db.host,
        port=db.port,
        dbname=db.database,
        user=db.user,
        password=db.password
    )
