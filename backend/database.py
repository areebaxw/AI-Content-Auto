from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from .config import settings
except ImportError:  # pragma: no cover - script execution fallback
    from config import settings

DATABASE_PATH = Path(settings.database_path)


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


@contextmanager
def get_connection() -> Iterable[sqlite3.Connection]:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = _dict_factory
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                original_content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft'
            );

            CREATE TABLE IF NOT EXISTS generated_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                variant_index INTEGER NOT NULL,
                generated_content TEXT NOT NULL,
                edited_content TEXT,
                posted_at TIMESTAMP NULL,
                post_url TEXT,
                engagement_count INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'draft',
                error_message TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            );

            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                scheduled_time TIMESTAMP NOT NULL,
                posted INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'scheduled',
                last_attempt_at TIMESTAMP NULL,
                FOREIGN KEY (post_id) REFERENCES generated_posts (id)
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
            ("default_timezone", settings.timezone),
        )


def save_campaign(title: str, original_content: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO campaigns (title, original_content, created_at, status)
            VALUES (?, ?, ?, 'draft')
            """,
            (title, original_content, datetime.utcnow().isoformat()),
        )
        return int(cursor.lastrowid)


def save_generated_posts(campaign_id: int, posts: Dict[str, Any]) -> List[Dict[str, Any]]:
    created_posts: List[Dict[str, Any]] = []
    with get_connection() as connection:
        for platform, value in posts.items():
            if platform == "email":
                values = [json.dumps(value)]
            elif isinstance(value, list):
                values = value
            else:
                values = [value]

            for index, content in enumerate(values):
                cursor = connection.execute(
                    """
                    INSERT INTO generated_posts
                    (campaign_id, platform, variant_index, generated_content, edited_content, status)
                    VALUES (?, ?, ?, ?, ?, 'draft')
                    """,
                    (campaign_id, platform, index, content, content),
                )
                created_posts.append(
                    {
                        "id": int(cursor.lastrowid),
                        "campaign_id": campaign_id,
                        "platform": platform,
                        "variant_index": index,
                        "generated_content": content,
                        "edited_content": content,
                        "status": "draft",
                    }
                )
    return created_posts


def update_post_content(post_id: int, edited_content: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE generated_posts SET edited_content = ?, status = 'draft' WHERE id = ?",
            (edited_content, post_id),
        )


def mark_post_posted(post_id: int, post_url: str = "") -> None:
    now = datetime.utcnow().isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE generated_posts
            SET posted_at = ?, post_url = ?, status = 'posted', error_message = NULL
            WHERE id = ?
            """,
            (now, post_url, post_id),
        )


def create_schedule(post_id: int, platform: str, scheduled_time: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO schedules (post_id, platform, scheduled_time, posted, status)
            VALUES (?, ?, ?, 0, 'scheduled')
            """,
            (post_id, platform, scheduled_time),
        )
        connection.execute(
            "UPDATE generated_posts SET status = 'scheduled' WHERE id = ?",
            (post_id,),
        )
        return int(cursor.lastrowid)


def get_due_schedules(now_iso: str) -> List[Dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT s.id AS schedule_id, s.post_id, s.platform, s.scheduled_time, s.posted,
                   p.edited_content, p.generated_content, p.campaign_id
            FROM schedules AS s
            JOIN generated_posts AS p ON p.id = s.post_id
            WHERE s.posted = 0 AND s.scheduled_time <= ?
            ORDER BY s.scheduled_time ASC
            """,
            (now_iso,),
        )
        return list(cursor.fetchall())


def mark_schedule_attempt(schedule_id: int, status: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE schedules SET status = ?, last_attempt_at = ? WHERE id = ?",
            (status, datetime.utcnow().isoformat(), schedule_id),
        )


def mark_schedule_posted(schedule_id: int, post_id: int, post_url: str) -> None:
    now = datetime.utcnow().isoformat()
    with get_connection() as connection:
        connection.execute(
            "UPDATE schedules SET posted = 1, status = 'posted', last_attempt_at = ? WHERE id = ?",
            (now, schedule_id),
        )
        connection.execute(
            """
            UPDATE generated_posts
            SET posted_at = ?, post_url = ?, status = 'posted', error_message = NULL
            WHERE id = ?
            """,
            (now, post_url, post_id),
        )
        connection.execute(
            "UPDATE campaigns SET status = 'posted' WHERE id = (SELECT campaign_id FROM generated_posts WHERE id = ?)",
            (post_id,),
        )


def mark_post_failed(post_id: int, error_message: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE generated_posts SET status = 'failed', error_message = ? WHERE id = ?",
            (error_message, post_id),
        )
        connection.execute(
            "UPDATE campaigns SET status = 'draft' WHERE id = (SELECT campaign_id FROM generated_posts WHERE id = ?)",
            (post_id,),
        )


def list_campaigns() -> List[Dict[str, Any]]:
    with get_connection() as connection:
        campaigns = list(
            connection.execute(
                "SELECT * FROM campaigns ORDER BY created_at DESC"
            ).fetchall()
        )
        for campaign in campaigns:
            posts = list(
                connection.execute(
                    "SELECT * FROM generated_posts WHERE campaign_id = ? ORDER BY platform, variant_index",
                    (campaign["id"],),
                ).fetchall()
            )
            campaign["posts"] = posts
        return campaigns


def list_generated_posts(campaign_id: int) -> List[Dict[str, Any]]:
    with get_connection() as connection:
        return list(
            connection.execute(
                "SELECT * FROM generated_posts WHERE campaign_id = ? ORDER BY platform, variant_index",
                (campaign_id,),
            ).fetchall()
        )


def list_schedules() -> List[Dict[str, Any]]:
    with get_connection() as connection:
        return list(
            connection.execute(
                "SELECT * FROM schedules ORDER BY scheduled_time DESC"
            ).fetchall()
        )


def get_app_settings() -> Dict[str, str]:
    with get_connection() as connection:
        rows = connection.execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def update_app_setting(key: str, value: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
