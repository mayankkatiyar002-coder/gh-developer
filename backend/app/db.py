"""SQLite caching engine.

Tables
------
cache          : generic key/value JSON cache with TTL (profile, repos, contributions)
repositories   : normalised repo metadata per user (used by match engine & chatbot)
user_settings  : per-user preferences (e.g. last job description, theme)
"""
import json
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Optional

from .config import CACHE_TTL, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS repositories (
    username    TEXT NOT NULL,
    name        TEXT NOT NULL,
    description TEXT,
    language    TEXT,
    languages   TEXT,          -- JSON {lang: bytes}
    topics      TEXT,          -- JSON list
    stars       INTEGER DEFAULT 0,
    forks       INTEGER DEFAULT 0,
    url         TEXT,
    updated_at  TEXT,
    PRIMARY KEY (username, name)
);
CREATE TABLE IF NOT EXISTS user_settings (
    username TEXT NOT NULL,
    key      TEXT NOT NULL,
    value    TEXT,
    PRIMARY KEY (username, key)
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as c:
        c.executescript(SCHEMA)


# ---------- generic cache ----------
def cache_get(key: str, ttl: int = CACHE_TTL) -> Optional[Any]:
    with get_conn() as c:
        row = c.execute("SELECT value, updated_at FROM cache WHERE key=?", (key,)).fetchone()
    if row and (time.time() - row["updated_at"]) < ttl:
        return json.loads(row["value"])
    return None


def cache_set(key: str, value: Any) -> None:
    with get_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO cache(key, value, updated_at) VALUES (?,?,?)",
            (key, json.dumps(value), time.time()),
        )


def cache_clear(prefix: str) -> None:
    with get_conn() as c:
        c.execute("DELETE FROM cache WHERE key LIKE ?", (f"{prefix}%",))


# ---------- repositories ----------
def save_repositories(username: str, repos: list[dict]) -> None:
    with get_conn() as c:
        c.execute("DELETE FROM repositories WHERE username=?", (username.lower(),))
        c.executemany(
            """INSERT INTO repositories
               (username,name,description,language,languages,topics,stars,forks,url,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            [
                (
                    username.lower(), r["name"], r.get("description"), r.get("language"),
                    json.dumps(r.get("languages", {})), json.dumps(r.get("topics", [])),
                    r.get("stars", 0), r.get("forks", 0), r.get("url"), r.get("updated_at"),
                )
                for r in repos
            ],
        )


def load_repositories(username: str) -> list[dict]:
    with get_conn() as c:
        rows = c.execute(
            "SELECT * FROM repositories WHERE username=? ORDER BY stars DESC", (username.lower(),)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["languages"] = json.loads(d["languages"] or "{}")
        d["topics"] = json.loads(d["topics"] or "[]")
        out.append(d)
    return out


# ---------- user settings ----------
def set_setting(username: str, key: str, value: str) -> None:
    with get_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO user_settings(username,key,value) VALUES (?,?,?)",
            (username.lower(), key, value),
        )


def get_settings(username: str) -> dict:
    with get_conn() as c:
        rows = c.execute(
            "SELECT key, value FROM user_settings WHERE username=?", (username.lower(),)
        ).fetchall()
    return {r["key"]: r["value"] for r in rows}
